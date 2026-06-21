from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from backend.app.models.database import get_db
from backend.app.core.agent import run_agent
import uuid
import json
from datetime import datetime
from backend.app.models.chat import ChatRequest

router = APIRouter(prefix="/api/chat", tags=["chat"])


async def _ensure_session(db, req: ChatRequest) -> str:
    now = datetime.now().isoformat()
    if req.session_id:
        row = await db.execute("SELECT id FROM chat_sessions WHERE id=?", [req.session_id])
        session = await row.fetchone()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        await db.execute("UPDATE chat_sessions SET updated_at=? WHERE id=?", [now, req.session_id])
        return req.session_id

    session_id = str(uuid.uuid4())
    title = req.message.strip()[:40] or "新会话"
    await db.execute(
        "INSERT INTO chat_sessions (id, title, service_id, message_count, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        [session_id, title, req.service_id, 0, now, now],
    )
    return session_id


async def _load_history(db, session_id: str) -> list:
    rows = await db.execute(
        """
        SELECT role, content FROM chat_messages
        WHERE session_id=? AND role IN ('user', 'assistant') AND content != ''
        ORDER BY timestamp ASC
        LIMIT 40
        """,
        [session_id],
    )
    return [{"role": r["role"], "content": r["content"]} async for r in rows]


async def _insert_chat_message(db, session_id: str, role: str, content: str,
                               thinking: str = None, tool_calls: list = None):
    await db.execute(
        """
        INSERT INTO chat_messages (id, session_id, role, content, thinking, tool_calls, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            str(uuid.uuid4()),
            session_id,
            role,
            content,
            thinking,
            json.dumps(tool_calls or [], ensure_ascii=False),
            datetime.now().isoformat(),
        ],
    )


async def _refresh_session_count(db, session_id: str):
    await db.execute(
        """
        UPDATE chat_sessions
        SET message_count=(SELECT COUNT(*) FROM chat_messages WHERE session_id=?),
            updated_at=?
        WHERE id=?
        """,
        [session_id, datetime.now().isoformat(), session_id],
    )

@router.post("/send")
async def send_message(req: ChatRequest):
    db = await get_db()
    session_id = await _ensure_session(db, req)
    history = await _load_history(db, session_id)
    await _insert_chat_message(db, session_id, "user", req.message)
    await _refresh_session_count(db, session_id)
    await db.commit()
    await db.close()

    # 获取工具列表
    tools = []
    if req.service_id:
        db = await get_db()
        rows = await db.execute(
            """
            SELECT id, service_id, name, description, parameters_schema, enabled, call_count
            FROM tools
            WHERE service_id=? AND enabled=1
            """,
            [req.service_id],
        )
        async for r in rows:
            d = dict(r)
            d["parameters_schema"] = json.loads(d["parameters_schema"])
            tools.append(d)
        await db.close()

    async def event_stream():
        yield f"event: session\ndata: {json.dumps({'session_id': session_id})}\n\n"

        assistant_content = ""
        assistant_thinking = None
        assistant_tool_calls = []

        try:
            async for event in run_agent(
                message=req.message,
                tools=tools,
                llm_api_key=req.llm_api_key,
                model=req.model,
                history=history,
                llm_base_url=req.llm_base_url,
                service_id=req.service_id,
            ):
                event_type = event["event"]
                try:
                    event_data = json.loads(event["data"])
                except json.JSONDecodeError:
                    event_data = {}

                if event_type == "message":
                    assistant_content += event_data.get("content", "")
                elif event_type == "thinking":
                    assistant_thinking = event_data.get("content")
                elif event_type == "tool_call":
                    assistant_tool_calls.append(event_data)
                elif event_type == "tool_result":
                    for tool_call in assistant_tool_calls:
                        if tool_call.get("id") == event_data.get("id"):
                            tool_call.update(event_data)
                            break

                yield f"event: {event_type}\ndata: {event['data']}\n\n"
        finally:
            db2 = await get_db()
            await _insert_chat_message(
                db2,
                session_id,
                "assistant",
                assistant_content,
                assistant_thinking,
                assistant_tool_calls,
            )
            await _refresh_session_count(db2, session_id)
            await db2.commit()
            await db2.close()

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/sessions")
async def list_sessions():
    db = await get_db()
    rows = await db.execute("SELECT * FROM chat_sessions ORDER BY updated_at DESC")
    result = [dict(r) async for r in rows]
    await db.close()
    return result


@router.get("/sessions/{session_id}/messages")
async def get_messages(session_id: str):
    db = await get_db()
    rows = await db.execute("SELECT * FROM chat_messages WHERE session_id=? ORDER BY timestamp", [session_id])
    result = []
    async for r in rows:
        d = dict(r)
        d["tool_calls"] = json.loads(d["tool_calls"])
        result.append(d)
    await db.close()
    return result


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    db = await get_db()
    await db.execute("DELETE FROM chat_messages WHERE session_id=?", [session_id])
    await db.execute("DELETE FROM chat_sessions WHERE id=?", [session_id])
    await db.commit()
    await db.close()
    return {"message": "ok"}

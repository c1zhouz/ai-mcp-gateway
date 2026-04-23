from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.app.models.database import get_db
from backend.app.core.agent import run_agent
import uuid
import json
from datetime import datetime
from typing import Optional, List, Dict
from backend.app.models.chat import ChatRequest

router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post("/send")
async def send_message(req: ChatRequest):
    # 获取工具列表
    tools = []
    if req.service_id:
        db = await get_db()
        rows = await db.execute("SELECT * FROM tools WHERE service_id=? AND enabled=1", [req.service_id])
        async for r in rows:
            d = dict(r)
            d["parameters_schema"] = json.loads(d["parameters_schema"])
            tools.append(d)
        await db.close()

    async def event_stream():
        async for event in run_agent(
            message=req.message,
            tools=tools,
            llm_api_key=req.llm_api_key,
            model=req.model,
            llm_base_url=req.llm_base_url,
        ):
            yield f"event: {event['event']}\ndata: {event['data']}\n\n"

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

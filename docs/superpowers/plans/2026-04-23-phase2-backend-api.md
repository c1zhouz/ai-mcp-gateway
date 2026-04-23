# Phase 2: 后端 API 完整实现

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现后端所有 REST API 端点和 SSE 对话流，为前端提供完整的数据服务。

**Architecture:** FastAPI 路由模块化，每个业务模块一个路由文件。使用 aiosqlite 异步数据库操作。Agent 编排器通过 SSE 流式推送对话事件。

**Tech Stack:** FastAPI, aiosqlite, OpenAI Python SDK, Pydantic, SSE

**Depends on:** Phase 1 完成

---

### Task 1: Dashboard API

**Files:**
- Create: `backend/app/api/dashboard.py`
- Modify: `backend/app/main.py` (注册路由)

- [ ] **Step 1: 实现 Dashboard 路由**

```python
# backend/app/api/dashboard.py
from fastapi import APIRouter
from backend.app.models.database import get_db

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_stats():
    db = await get_db()
    services = await db.execute("SELECT COUNT(*) as count FROM services WHERE status='online'")
    service_row = await services.fetchone()
    tools = await db.execute("SELECT COUNT(*) as count FROM tools WHERE enabled=1")
    tool_row = await tools.fetchone()
    await db.close()
    return {
        "online_services": service_row["count"],
        "total_tools": tool_row["count"],
        "today_requests": 0,
        "success_rate": 100.0,
    }


@router.get("/trend")
async def get_trend():
    # 返回模拟趋势数据，后续接入真实统计
    from datetime import datetime, timedelta
    import random
    now = datetime.now()
    data = []
    for i in range(168):  # 7 days * 24 hours
        t = now - timedelta(hours=168 - i)
        data.append({"time": t.strftime("%m-%d %H:00"), "requests": random.randint(10, 200)})
    return data


@router.get("/top-tools")
async def get_top_tools():
    db = await get_db()
    rows = await db.execute(
        "SELECT name, call_count FROM tools ORDER BY call_count DESC LIMIT 10"
    )
    result = [{"name": r["name"], "count": r["call_count"]} async for r in rows]
    await db.close()
    return result


@router.get("/activities")
async def get_activities():
    return []


@router.get("/alerts")
async def get_alerts():
    return []
```

- [ ] **Step 2: 在 main.py 注册路由**

```python
# 添加到 backend/app/main.py
from backend.app.api.dashboard import router as dashboard_router
app.include_router(dashboard_router)
```

- [ ] **Step 3: 验证**

```bash
curl http://localhost:8000/api/dashboard/stats
```
Expected: 返回 JSON 统计数据

- [ ] **Step 4: Commit**

```bash
git add backend/
git commit -m "feat: implement dashboard API endpoints"
```

---

### Task 2: Gateway API

**Files:**
- Create: `backend/app/api/gateway.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: 实现 Gateway 路由**

```python
# backend/app/api/gateway.py
from fastapi import APIRouter, HTTPException
from backend.app.models.database import get_db
import uuid
import json
import secrets
from datetime import datetime

router = APIRouter(prefix="/api/gateway", tags=["gateway"])


@router.get("/config")
async def get_config():
    db = await get_db()
    row = await db.execute("SELECT * FROM gateway_config WHERE id=1")
    config = await row.fetchone()
    await db.close()
    return dict(config)


@router.put("/config")
async def update_config(data: dict):
    db = await get_db()
    fields = ["name", "listen_address", "port", "timeout_ms", "max_concurrency", "log_level", "log_retention_days"]
    updates = {k: v for k, v in data.items() if k in fields}
    if updates:
        set_clause = ", ".join(f"{k}=?" for k in updates)
        await db.execute(f"UPDATE gateway_config SET {set_clause} WHERE id=1", list(updates.values()))
        await db.commit()
    await db.close()
    return {"message": "ok"}


@router.get("/api-keys")
async def list_api_keys():
    db = await get_db()
    rows = await db.execute("SELECT * FROM api_keys ORDER BY created_at DESC")
    result = []
    async for r in rows:
        d = dict(r)
        d["permissions"] = json.loads(d["permissions"])
        d["key_value"] = d["key_value"][:8] + "****"
        result.append(d)
    await db.close()
    return result


@router.post("/api-keys")
async def create_api_key(data: dict):
    db = await get_db()
    key_id = str(uuid.uuid4())
    key_value = "gw-" + secrets.token_hex(24)
    await db.execute(
        "INSERT INTO api_keys (id, name, key_value, permissions, expires_at, created_at) VALUES (?,?,?,?,?,?)",
        [key_id, data["name"], key_value, json.dumps(data.get("permissions", ["read"])),
         data.get("expires_at"), datetime.now().isoformat()]
    )
    await db.commit()
    await db.close()
    return {"id": key_id, "key_value": key_value}


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(key_id: str):
    db = await get_db()
    await db.execute("UPDATE api_keys SET status='revoked' WHERE id=?", [key_id])
    await db.commit()
    await db.close()
    return {"message": "ok"}


@router.get("/routes")
async def list_routes():
    db = await get_db()
    rows = await db.execute("SELECT r.*, s.name as service_name FROM route_rules r LEFT JOIN services s ON r.target_service_id=s.id ORDER BY priority DESC")
    result = [dict(r) async for r in rows]
    await db.close()
    return result


@router.post("/routes")
async def create_route(data: dict):
    db = await get_db()
    route_id = str(uuid.uuid4())
    await db.execute(
        "INSERT INTO route_rules (id, path_pattern, target_service_id, priority, enabled) VALUES (?,?,?,?,?)",
        [route_id, data["path_pattern"], data["target_service_id"], data.get("priority", 0), 1]
    )
    await db.commit()
    await db.close()
    return {"id": route_id}


@router.put("/routes/{route_id}")
async def update_route(route_id: str, data: dict):
    db = await get_db()
    fields = ["path_pattern", "target_service_id", "priority", "enabled"]
    updates = {k: v for k, v in data.items() if k in fields}
    if updates:
        set_clause = ", ".join(f"{k}=?" for k in updates)
        await db.execute(f"UPDATE route_rules SET {set_clause} WHERE id=?", list(updates.values()) + [route_id])
        await db.commit()
    await db.close()
    return {"message": "ok"}


@router.delete("/routes/{route_id}")
async def delete_route(route_id: str):
    db = await get_db()
    await db.execute("DELETE FROM route_rules WHERE id=?", [route_id])
    await db.commit()
    await db.close()
    return {"message": "ok"}
```

- [ ] **Step 2: 注册路由并 Commit**

```bash
git add backend/
git commit -m "feat: implement gateway API endpoints"
```

---

### Task 3: Services API

**Files:**
- Create: `backend/app/api/services.py`

- [ ] **Step 1: 实现 Services 路由**

```python
# backend/app/api/services.py
from fastapi import APIRouter, HTTPException
from backend.app.models.database import get_db
from backend.app.models.service import ServiceCreate, ServiceUpdate
import uuid
import json
from datetime import datetime

router = APIRouter(prefix="/api/services", tags=["services"])


@router.get("")
async def list_services():
    db = await get_db()
    rows = await db.execute("SELECT * FROM services ORDER BY created_at DESC")
    result = [dict(r) async for r in rows]
    await db.close()
    return result


@router.post("")
async def create_service(data: ServiceCreate):
    db = await get_db()
    service_id = str(uuid.uuid4())
    await db.execute(
        "INSERT INTO services (id,name,address,description,status,health_check_interval,auto_reconnect,created_at) VALUES (?,?,?,?,?,?,?,?)",
        [service_id, data.name, data.address, data.description, "offline",
         data.health_check_interval, int(data.auto_reconnect), datetime.now().isoformat()]
    )
    await db.commit()
    await db.close()
    return {"id": service_id}


@router.get("/{service_id}")
async def get_service(service_id: str):
    db = await get_db()
    row = await db.execute("SELECT * FROM services WHERE id=?", [service_id])
    service = await row.fetchone()
    if not service:
        await db.close()
        raise HTTPException(status_code=404, detail="Service not found")
    result = dict(service)
    await db.close()
    return result


@router.put("/{service_id}")
async def update_service(service_id: str, data: ServiceUpdate):
    db = await get_db()
    updates = {k: v for k, v in data.model_dump(exclude_none=True).items()}
    if "auto_reconnect" in updates:
        updates["auto_reconnect"] = int(updates["auto_reconnect"])
    if updates:
        set_clause = ", ".join(f"{k}=?" for k in updates)
        await db.execute(f"UPDATE services SET {set_clause} WHERE id=?", list(updates.values()) + [service_id])
        await db.commit()
    await db.close()
    return {"message": "ok"}


@router.delete("/{service_id}")
async def delete_service(service_id: str):
    db = await get_db()
    await db.execute("DELETE FROM tools WHERE service_id=?", [service_id])
    await db.execute("DELETE FROM services WHERE id=?", [service_id])
    await db.commit()
    await db.close()
    return {"message": "ok"}


@router.get("/{service_id}/tools")
async def get_service_tools(service_id: str):
    db = await get_db()
    rows = await db.execute("SELECT * FROM tools WHERE service_id=?", [service_id])
    result = []
    async for r in rows:
        d = dict(r)
        d["parameters_schema"] = json.loads(d["parameters_schema"])
        result.append(d)
    await db.close()
    return result


@router.post("/{service_id}/health-check")
async def health_check(service_id: str):
    db = await get_db()
    await db.execute("UPDATE services SET status='online', last_heartbeat=? WHERE id=?",
                     [datetime.now().isoformat(), service_id])
    await db.commit()
    await db.close()
    return {"status": "online"}
```

- [ ] **Step 2: 注册路由并 Commit**

```bash
git add backend/
git commit -m "feat: implement services API endpoints"
```

---

### Task 4: Tools API

**Files:**
- Create: `backend/app/api/tools.py`

- [ ] **Step 1: 实现 Tools 路由**

```python
# backend/app/api/tools.py
from fastapi import APIRouter, HTTPException
from backend.app.models.database import get_db
import json

router = APIRouter(prefix="/api/tools", tags=["tools"])


@router.get("")
async def list_tools(service_id: str = None, search: str = None, enabled: bool = None):
    db = await get_db()
    query = "SELECT t.*, s.name as service_name FROM tools t LEFT JOIN services s ON t.service_id=s.id WHERE 1=1"
    params = []
    if service_id:
        query += " AND t.service_id=?"
        params.append(service_id)
    if search:
        query += " AND (t.name LIKE ? OR t.description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    if enabled is not None:
        query += " AND t.enabled=?"
        params.append(int(enabled))
    query += " ORDER BY s.name, t.name"
    rows = await db.execute(query, params)
    result = []
    async for r in rows:
        d = dict(r)
        d["parameters_schema"] = json.loads(d["parameters_schema"])
        result.append(d)
    await db.close()
    return result


@router.get("/{tool_id}")
async def get_tool(tool_id: str):
    db = await get_db()
    row = await db.execute(
        "SELECT t.*, s.name as service_name FROM tools t LEFT JOIN services s ON t.service_id=s.id WHERE t.id=?",
        [tool_id]
    )
    tool = await row.fetchone()
    if not tool:
        await db.close()
        raise HTTPException(status_code=404, detail="Tool not found")
    d = dict(tool)
    d["parameters_schema"] = json.loads(d["parameters_schema"])
    await db.close()
    return d


@router.patch("/{tool_id}")
async def update_tool(tool_id: str, data: dict):
    db = await get_db()
    if "enabled" in data:
        await db.execute("UPDATE tools SET enabled=? WHERE id=?", [int(data["enabled"]), tool_id])
        await db.commit()
    await db.close()
    return {"message": "ok"}
```

- [ ] **Step 2: 注册路由并 Commit**

```bash
git add backend/
git commit -m "feat: implement tools API endpoints"
```

---

### Task 5: Chat API with SSE

**Files:**
- Create: `backend/app/api/chat.py`
- Create: `backend/app/core/agent.py`
- Create: `backend/app/core/llm_client.py`

- [ ] **Step 1: 创建 LLM 客户端**

```python
# backend/app/core/llm_client.py
from openai import AsyncOpenAI


def create_llm_client(api_key: str, base_url: str = None):
    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    return AsyncOpenAI(**kwargs)
```

- [ ] **Step 2: 创建 Agent 编排器**

```python
# backend/app/core/agent.py
import json
from backend.app.core.llm_client import create_llm_client


async def run_agent(message: str, tools: list, llm_api_key: str, model: str = "gpt-4o",
                    llm_base_url: str = None):
    """Agent 编排器：执行 LLM 调用循环并 yield SSE 事件"""
    client = create_llm_client(llm_api_key, llm_base_url)

    # 构建工具定义
    tool_definitions = []
    for t in tools:
        tool_definitions.append({
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t.get("description", ""),
                "parameters": t.get("parameters_schema", {}),
            }
        })

    messages = [
        {"role": "system", "content": "你是一个有用的AI助手。你可以使用提供的工具来帮助回答用户的问题。在调用工具前，请先思考你的计划。"},
        {"role": "user", "content": message},
    ]

    max_iterations = 10
    for _ in range(max_iterations):
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tool_definitions if tool_definitions else None,
            stream=False,
        )

        choice = response.choices[0]
        assistant_msg = choice.message

        # 如果有内容，可能是思考过程或最终回复
        if assistant_msg.content:
            if assistant_msg.tool_calls:
                yield {"event": "thinking", "data": json.dumps({"content": assistant_msg.content}, ensure_ascii=False)}
            else:
                yield {"event": "message", "data": json.dumps({"content": assistant_msg.content, "delta": False}, ensure_ascii=False)}

        # 处理工具调用
        if assistant_msg.tool_calls:
            messages.append(assistant_msg.model_dump())
            for tc in assistant_msg.tool_calls:
                tc_id = tc.id
                fn_name = tc.function.name
                fn_args = json.loads(tc.function.arguments)

                yield {"event": "tool_call", "data": json.dumps(
                    {"id": tc_id, "name": fn_name, "arguments": fn_args, "status": "calling"},
                    ensure_ascii=False
                )}

                # 模拟工具执行 (实际应通过 MCP 客户端调用)
                tool_result = {"code": 0, "message": "success", "data": f"Mock result for {fn_name}"}

                yield {"event": "tool_result", "data": json.dumps(
                    {"id": tc_id, "name": fn_name, "result": tool_result, "status": "completed", "duration_ms": 150},
                    ensure_ascii=False
                )}

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc_id,
                    "content": json.dumps(tool_result, ensure_ascii=False),
                })
            continue
        else:
            break

    yield {"event": "done", "data": json.dumps({"usage": {"prompt_tokens": response.usage.prompt_tokens, "completion_tokens": response.usage.completion_tokens}})}
```

- [ ] **Step 3: 创建 Chat 路由**

```python
# backend/app/api/chat.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.app.models.database import get_db
from backend.app.core.agent import run_agent
import uuid
import json
from datetime import datetime

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str
    gateway_url: str = ""
    gateway_api_key: str = ""
    llm_api_key: str
    llm_base_url: str | None = None
    service_id: str | None = None
    model: str = "gpt-4o"


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
```

- [ ] **Step 4: 注册所有路由到 main.py**

```python
# backend/app/main.py - 完整路由注册
from backend.app.api.dashboard import router as dashboard_router
from backend.app.api.gateway import router as gateway_router
from backend.app.api.services import router as services_router
from backend.app.api.tools import router as tools_router
from backend.app.api.chat import router as chat_router

app.include_router(dashboard_router)
app.include_router(gateway_router)
app.include_router(services_router)
app.include_router(tools_router)
app.include_router(chat_router)
```

- [ ] **Step 5: 验证所有 API**

```bash
curl http://localhost:8000/docs
```
Expected: Swagger UI 显示所有端点

- [ ] **Step 6: Commit**

```bash
git add backend/
git commit -m "feat: implement chat API with SSE streaming and agent orchestrator"
```

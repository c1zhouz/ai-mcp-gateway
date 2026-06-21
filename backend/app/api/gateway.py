import fnmatch

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from backend.app.core.auth import hash_api_key, mask_api_key, require_api_key
from backend.app.core.mcp_client import execute_tool
from backend.app.models.database import get_db
from backend.app.core.logger import log_manager
import uuid
import json
import secrets
from datetime import datetime
from typing import Optional, List, Dict

router = APIRouter(prefix="/api/gateway", tags=["gateway"])
public_router = APIRouter(prefix="/gateway", tags=["gateway-entrypoint"])


def _normalize_gateway_path(path: str) -> str:
    clean = path.strip("/")
    return f"/{clean}" if clean else "/"


def _json_rpc_response(request_id, result=None, error=None):
    payload = {"jsonrpc": "2.0", "id": request_id}
    if error is not None:
        payload["error"] = error
    else:
        payload["result"] = result
    return payload


async def _match_route(path: str):
    normalized_path = _normalize_gateway_path(path)
    db = await get_db()
    rows = await db.execute("""
        SELECT r.*, s.address, s.name as service_name
        FROM route_rules r
        JOIN services s ON r.target_service_id=s.id
        WHERE r.enabled=1
        ORDER BY r.priority DESC
    """)
    async for row in rows:
        route = dict(row)
        pattern = _normalize_gateway_path(route["path_pattern"])
        if fnmatch.fnmatch(normalized_path, pattern):
            await db.close()
            return route
    await db.close()
    return None


async def _list_cached_tools(service_id: str):
    db = await get_db()
    rows = await db.execute(
        "SELECT name, description, parameters_schema FROM tools WHERE service_id=? AND enabled=1 ORDER BY name",
        [service_id],
    )
    tools = []
    async for row in rows:
        tool = dict(row)
        tools.append({
            "name": tool["name"],
            "description": tool["description"],
            "inputSchema": json.loads(tool["parameters_schema"]),
        })
    await db.close()
    return tools


@public_router.post("/{path:path}")
async def gateway_entrypoint(path: str, request: Request):
    payload = await request.json()
    request_id = payload.get("id")
    method = payload.get("method")

    route = await _match_route(path)
    if not route:
        raise HTTPException(status_code=404, detail="No route matched gateway path")

    if method == "tools/list":
        await require_api_key(request, "read")
        tools = await _list_cached_tools(route["target_service_id"])
        return _json_rpc_response(request_id, {"tools": tools})

    if method == "tools/call":
        await require_api_key(request, "write")
        params = payload.get("params") or {}
        tool_name = params.get("name")
        arguments = params.get("arguments") or {}
        if not tool_name:
            return _json_rpc_response(
                request_id,
                error={"code": -32602, "message": "Missing params.name"},
            )

        result = await execute_tool(route["address"], tool_name, arguments)
        if result.get("status") == "success":
            db = await get_db()
            await db.execute(
                "UPDATE tools SET call_count = call_count + 1 WHERE service_id=? AND name=?",
                [route["target_service_id"], tool_name],
            )
            await db.commit()
            await db.close()
            return _json_rpc_response(request_id, {"content": result.get("content", [])})

        return _json_rpc_response(
            request_id,
            error={"code": -32000, "message": result.get("error", "Tool execution failed")},
        )

    return _json_rpc_response(
        request_id,
        error={"code": -32601, "message": f"Unsupported method: {method}"},
    )


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
        d["key_value"] = mask_api_key(d["key_value"])
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
        [key_id, data["name"], hash_api_key(key_value), json.dumps(data.get("permissions", ["read"])),
         data.get("expires_at"), datetime.now().isoformat()]
    )
    await db.commit()
    await db.close()
    return {"id": key_id, "key_value": key_value}


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(key_id: str):
    db = await get_db()
    row = await db.execute("SELECT status FROM api_keys WHERE id=?", [key_id])
    key = await row.fetchone()
    if key and key["status"] == "active":
        await db.execute("UPDATE api_keys SET status='revoked' WHERE id=?", [key_id])
    else:
        await db.execute("DELETE FROM api_keys WHERE id=?", [key_id])
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


@router.get("/logs/stream")
async def stream_logs():
    async def event_generator():
        # 发送历史记录
        for entry in log_manager.history:
            yield f"data: {json.dumps(entry, ensure_ascii=False)}\n\n"
        
        # 持续发送新日志
        while True:
            # 这里的 get 是阻塞的，但由于是异步的，不会阻塞 event loop
            entry = await log_manager.queue.get()
            yield f"data: {json.dumps(entry, ensure_ascii=False)}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

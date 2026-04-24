from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from backend.app.models.database import get_db
from backend.app.core.logger import log_manager
import uuid
import json
import secrets
from datetime import datetime
from typing import Optional, List, Dict

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

from fastapi import APIRouter, HTTPException
from backend.app.models.database import get_db
from backend.app.models.service import ServiceCreate, ServiceUpdate
import uuid
import json
from datetime import datetime
from backend.app.core.mcp_client import sync_tools
from typing import Optional, List, Dict

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
    
    tools_list = await sync_tools(data.address)
    tool_count = len(tools_list)
    if tool_count > 0:
        for t in tools_list:
            await db.execute(
                """INSERT INTO tools (id, service_id, name, description, parameters_schema, enabled) 
                   VALUES (?, ?, ?, ?, ?, 1)""",
                [str(uuid.uuid4()), service_id, t["name"], t.get("description", ""), json.dumps(t.get("inputSchema", {}))]
            )
        await db.execute("UPDATE services SET tool_count = ?, status='online' WHERE id = ?", [tool_count, service_id])
    
    await db.commit()
    await db.close()
    return {"id": service_id, "tool_count": tool_count}


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

@router.post("/{service_id}/sync-tools")
async def sync_service_tools(service_id: str):
    db = await get_db()
    row = await db.execute("SELECT id, address FROM services WHERE id=?", [service_id])
    service = await row.fetchone()
    if not service:
        await db.close()
        raise HTTPException(status_code=404, detail="Service not found")
        
    tools_list = await sync_tools(service["address"])
    if not tools_list:
        await db.close()
        raise HTTPException(status_code=400, detail="No tools found or connection failed")
        
    await db.execute("DELETE FROM tools WHERE service_id=?", [service_id])
    
    for t in tools_list:
        await db.execute(
            """INSERT INTO tools (id, service_id, name, description, parameters_schema, enabled) 
               VALUES (?, ?, ?, ?, ?, 1)""",
            [str(uuid.uuid4()), service_id, t["name"], t.get("description", ""), json.dumps(t.get("inputSchema", {}))]
        )
    
    tool_count = len(tools_list)
    await db.execute("UPDATE services SET tool_count=?, status='online' WHERE id=?", [tool_count, service_id])
    await db.commit()
    await db.close()
    
    return {"status": "success", "tool_count": tool_count}


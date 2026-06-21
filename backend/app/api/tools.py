from fastapi import APIRouter, HTTPException
from backend.app.models.database import get_db
import json

router = APIRouter(prefix="/api/tools", tags=["tools"])

TOOL_SELECT = """
    SELECT
        t.id,
        t.service_id,
        t.name,
        t.description,
        t.parameters_schema,
        t.enabled,
        t.call_count,
        s.name as service_name
    FROM tools t
    LEFT JOIN services s ON t.service_id=s.id
"""


@router.get("")
async def list_tools(service_id: str = None, search: str = None, enabled: bool = None):
    db = await get_db()
    query = TOOL_SELECT + " WHERE 1=1"
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
        TOOL_SELECT + " WHERE t.id=?",
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
async def toggle_tool(tool_id: str, data: dict):
    db = await get_db()
    if "enabled" in data:
        await db.execute("UPDATE tools SET enabled=? WHERE id=?", [int(data["enabled"]), tool_id])
        await db.commit()
    await db.close()
    return {"message": "ok"}


@router.delete("/{tool_id}")
async def delete_tool(tool_id: str):
    db = await get_db()
    row = await db.execute("SELECT service_id FROM tools WHERE id=?", [tool_id])
    tool = await row.fetchone()
    if not tool:
        await db.close()
        raise HTTPException(status_code=404, detail="Tool not found")
    service_id = tool["service_id"]
    await db.execute("DELETE FROM tools WHERE id=?", [tool_id])
    await db.execute(
        "UPDATE services SET tool_count = (SELECT COUNT(*) FROM tools WHERE service_id=?) WHERE id=?",
        [service_id, service_id]
    )
    await db.commit()
    await db.close()
    return {"message": "删除成功"}

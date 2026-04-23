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
    from datetime import datetime, timedelta
    import random
    now = datetime.now()
    data = []
    for i in range(168):
        t = now - timedelta(hours=168 - i)
        data.append({"time": t.strftime("%m-%d %H:00"), "requests": random.randint(10, 200)})
    return data

@router.get("/top-tools")
async def get_top_tools():
    db = await get_db()
    rows = await db.execute("SELECT name, call_count FROM tools ORDER BY call_count DESC LIMIT 10")
    result = [{"name": r["name"], "count": r["call_count"]} async for r in rows]
    await db.close()
    return result

@router.get("/activities")
async def get_activities():
    return []

@router.get("/alerts")
async def get_alerts():
    return []

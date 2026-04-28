from fastapi import APIRouter
from backend.app.models.database import get_db
from backend.app.core.logger import log_manager
from datetime import datetime

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/stats")
async def get_stats():
    db = await get_db()
    services = await db.execute("SELECT COUNT(*) as count FROM services WHERE status='online'")
    service_row = await services.fetchone()
    
    # 获取今日总请求数和错误数 (基于 YYYY-MM-DD)
    today_str = datetime.now().strftime("%Y-%m-%d")
    requests = await db.execute("""
        SELECT SUM(count) as total_count, SUM(error_count) as total_errors 
        FROM request_history 
        WHERE time_hour LIKE ?
    """, [f"{today_str}%"])
    req_row = await requests.fetchone()
    
    total_req = req_row["total_count"] or 0
    total_err = req_row["total_errors"] or 0
    
    success_rate = 100.0
    if total_req > 0:
        success_rate = ((total_req - total_err) / total_req) * 100
        success_rate = max(0, success_rate) # 防止负数

    tools = await db.execute("SELECT COUNT(*) as count FROM tools WHERE enabled=1")
    tool_row = await tools.fetchone()
    await db.close()
    
    return {
        "online_services": service_row["count"],
        "total_tools": tool_row["count"],
        "today_requests": total_req,
        "success_rate": round(success_rate, 2),
    }

@router.get("/trend")
async def get_trend():
    from datetime import datetime, timedelta
    db = await get_db()
    
    # 获取最近 24 小时的数据
    now = datetime.now()
    start_time = (now - timedelta(hours=24)).strftime("%Y-%m-%d %H:00")
    
    rows = await db.execute("""
        SELECT time_hour, count FROM request_history 
        WHERE time_hour >= ? 
        ORDER BY time_hour ASC
    """, [start_time])
    
    db_data = {r["time_hour"]: r["count"] async for r in rows}
    await db.close()
    
    # 填充缺失的小时
    result = []
    for i in range(24):
        t = now - timedelta(hours=23 - i)
        ts = t.strftime("%Y-%m-%d %H:00")
        display_ts = t.strftime("%H:00") # 只显示小时
        result.append({
            "time": display_ts, 
            "requests": db_data.get(ts, 0)
        })
    return result

@router.get("/top-tools")
async def get_top_tools():
    db = await get_db()
    # 聚合相同名称的工具，并只显示调用次数大于 0 的
    rows = await db.execute("""
        SELECT name, SUM(call_count) as total_count 
        FROM tools 
        GROUP BY name 
        HAVING total_count > 0
        ORDER BY total_count DESC 
        LIMIT 10
    """)
    result = [{"name": r["name"], "count": r["total_count"]} async for r in rows]
    await db.close()
    return result

@router.get("/activities")
async def get_activities():
    return list(log_manager.history)

@router.get("/alerts")
async def get_alerts():
    # 模拟一些基于状态的告警
    alerts = []
    db = await get_db()
    offline_services = await db.execute("SELECT name FROM services WHERE status='offline'")
    async for row in offline_services:
        alerts.append({"type": "error", "text": f"微服务 [{row['name']}] 目前处于离线状态"})
    await db.close()
    
    if not alerts:
        alerts.append({"type": "success", "text": "系统所有核心组件运行良好"})
    return alerts

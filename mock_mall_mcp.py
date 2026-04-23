from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import json
import asyncio
import uvicorn

app = FastAPI()
clients = {}

@app.get("/sse")
async def sse_endpoint(request: Request):
    session_id = "test-mall-session"
    q = asyncio.Queue()
    clients[session_id] = q
    
    async def event_publisher():
        # MCP Protocol: first event must be 'endpoint'
        yield f"event: endpoint\ndata: /message?session_id={session_id}\n\n".encode("utf-8")
        
        try:
            while True:
                if await request.is_disconnected():
                    break
                data = await q.get()
                yield f"event: message\ndata: {json.dumps(data)}\n\n".encode("utf-8")
        except asyncio.CancelledError:
            pass
        finally:
            clients.pop(session_id, None)

    return StreamingResponse(event_publisher(), media_type="text/event-stream")

@app.post("/message")
async def message_endpoint(request: Request, session_id: str):
    data = await request.json()
    q = clients.get(session_id)
    if not q:
        return {"status": "error", "message": "session not found"}
        
    method = data.get("method")
    req_id = data.get("id")
    
    if method == "initialize":
        await q.put({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "serverInfo": {"name": "Mall-MCP-Server", "version": "1.0.0"}
            }
        })
    elif method == "notifications/initialized":
        pass
    elif method == "tools/list":
        await q.put({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "check_low_inventory",
                        "description": "获取商城当前库存低于预警阈值的商品列表",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "threshold": {
                                    "type": "integer", 
                                    "description": "库存报警阈值（默认10）"
                                }
                            }
                        }
                    },
                    {
                        "name": "get_sales_stats",
                        "description": "获取商城近期的销售统计数据报表",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "days": {
                                    "type": "integer", 
                                    "description": "查询最近几天的统计（默认7天）"
                                }
                            }
                        }
                    }
                ]
            }
        })
    elif method == "tools/call":
        tool_name = data.get("params", {}).get("name")
        args = data.get("params", {}).get("arguments", {})
        
        if tool_name == "check_low_inventory":
            threshold = args.get("threshold", 10)
            # 这里模拟查询商城数据库
            content = f"📉 预警：查询到以下商品库存低于 {threshold} 件：\n1. iPhone 15 Pro (仅剩 2 台)\n2. 游戏机械键盘 (仅剩 5 把)\n3. 飞利浦电动牙刷刷头 (仅剩 1 个)"
        elif tool_name == "get_sales_stats":
            days = args.get("days", 7)
            # 这里模拟聚合销售数据
            content = f"📊 销售报告：过去 {days} 天，商城总销售额为 ¥128,500，总订单量 1024 单。相比上一周期增长 12%。热销榜首是：戴森吹风机。"
        else:
            content = f"Error: 未知工具 {tool_name}"
            
        await q.put({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [
                    {"type": "text", "text": content}
                ]
            }
        })
        
    return "ok"

if __name__ == "__main__":
    print("启动模拟商城 MCP 微服务在 http://127.0.0.1:5001 ...")
    uvicorn.run(app, host="127.0.0.1", port=5001)

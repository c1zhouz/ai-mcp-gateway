import json
import time
from datetime import datetime
from backend.app.core.llm_client import create_llm_client
from backend.app.core.mcp_client import execute_tool
from backend.app.models.database import get_db
from backend.app.core.logger import log_manager

async def run_agent(message: str, tools: list, llm_api_key: str, model: str = "gpt-4o",
                    llm_base_url: str = None, service_id: str = None):
    """Agent 编排器：执行 LLM 调用循环并 yield SSE 事件"""
    
    # 记录一次请求
    db = await get_db()
    now_hour = datetime.now().strftime("%Y-%m-%d %H:00")
    await db.execute("""
        INSERT INTO request_history (time_hour, count) 
        VALUES (?, 1) 
        ON CONFLICT(time_hour) DO UPDATE SET count = count + 1
    """, [now_hour])
    await db.commit()
    await db.close()

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

                await log_manager.log(f"正在通过 MCP 调用工具: {fn_name}", "TOOL")

                # Execute via MCP Client
                start_time = time.time()
                tool_result = {"status": "error", "error": "Unknown error"}
                
                if service_id:
                    db = await get_db()
                    service_row = await db.execute("SELECT address FROM services WHERE id = ?", [service_id])
                    service = await service_row.fetchone()
                    if service:
                        service_url = service["address"]
                        # Execute real tool
                        exec_result = await execute_tool(service_url, fn_name, fn_args)
                        
                        if exec_result.get("status") == "success":
                            tool_result = exec_result.get("content", exec_result)
                            # Update call count
                            await db.execute("UPDATE tools SET call_count = call_count + 1 WHERE name = ? AND service_id = ?", [fn_name, service_id])
                            await db.commit()
                        else:
                            tool_result = exec_result
                            # 记录一次错误
                            await db.execute("UPDATE request_history SET error_count = error_count + 1 WHERE time_hour = ?", [datetime.now().strftime("%Y-%m-%d %H:00")])
                            await db.commit()
                    else:
                        tool_result = {"status": "error", "error": "Service not found in DB"}
                        await db.execute("UPDATE request_history SET error_count = error_count + 1 WHERE time_hour = ?", [datetime.now().strftime("%Y-%m-%d %H:00")])
                        await db.commit()
                    await db.close()
                else:
                    tool_result = {"status": "error", "error": "No service_id provided for tool call"}

                duration_ms = int((time.time() - start_time) * 1000)

                yield {"event": "tool_result", "data": json.dumps(
                    {"id": tc_id, "name": fn_name, "result": tool_result, "status": "completed", "duration_ms": duration_ms},
                    ensure_ascii=False
                )}

                await log_manager.log(f"工具 {fn_name} 调用成功，耗时 {duration_ms}ms", "TOOL")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc_id,
                    "content": json.dumps(tool_result, ensure_ascii=False),
                })
            continue
        else:
            break

    yield {"event": "done", "data": json.dumps({"usage": {"prompt_tokens": response.usage.prompt_tokens, "completion_tokens": response.usage.completion_tokens}})}

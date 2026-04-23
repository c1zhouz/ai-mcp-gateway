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

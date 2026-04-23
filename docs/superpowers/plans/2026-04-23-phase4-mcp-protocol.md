# Phase 4: MCP Protocol Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 AI 网关与后端微服务之间的真实 MCP 协议（基于 SSE 传输）的工具同步和执行调度。

**Architecture:** 后端利用 `mcp` Python SDK 实现 SSE Client 进行工具拉取与执行；在 `ChatAgent` 中插入动态路由层，拦截 LLM 的 Tool Call 请求转发给微服务，并将真实结果返回给 LLM 与前端流。

**Tech Stack:** Python 3.9+, FastAPI, mcp (Python SDK), SQLite, React, Ant Design

---

### Task 1: 安装依赖并封装 MCP Client

**Files:**
- Modify: `backend/requirements.txt`
- Create: `backend/app/core/mcp_client.py`

- [ ] **Step 1: 安装并配置依赖**

```bash
# Add mcp sdk and contextlib to requirements
echo "mcp==1.0.0" >> backend/requirements.txt
```

- [ ] **Step 2: 编写 mcp_client.py 封装**

由于底层 SDK 的用法，我们将使用标准库 `httpx` + `httpx_sse` 或者 `mcp` 的 client 包来发起连接。为简化，这里提供一个易于测试的包装器实现：

```python
# backend/app/core/mcp_client.py
import asyncio
from typing import List, Dict, Any
from mcp import ClientSession
from mcp.client.sse import sse_client

async def sync_tools(service_url: str) -> List[Dict]:
    """Connect to MCP service via SSE and list tools."""
    # Append /sse if not present, assume MCP servers expose /sse endpoint
    sse_url = service_url if service_url.endswith("/sse") else f"{service_url.rstrip('/')}/sse"
    
    try:
        async with sse_client(sse_url) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                tools_response = await session.list_tools()
                
                tools_list = []
                for t in tools_response.tools:
                    tools_list.append({
                        "name": t.name,
                        "description": t.description,
                        "inputSchema": t.inputSchema
                    })
                return tools_list
    except Exception as e:
        print(f"Failed to sync tools from {service_url}: {e}")
        return []

async def execute_tool(service_url: str, tool_name: str, arguments: dict) -> dict:
    """Connect to MCP service, call a tool, and close connection."""
    sse_url = service_url if service_url.endswith("/sse") else f"{service_url.rstrip('/')}/sse"
    
    try:
        async with sse_client(sse_url) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                # Convert CallToolResult to dict
                content = []
                for item in result.content:
                    if item.type == "text":
                        content.append({"type": "text", "text": item.text})
                return {"status": "success", "content": content}
    except Exception as e:
        print(f"Failed to execute tool {tool_name} on {service_url}: {e}")
        return {"status": "error", "error": str(e)}
```

- [ ] **Step 3: Commit**

```bash
git add backend/requirements.txt backend/app/core/mcp_client.py
git commit -m "feat: add mcp client wrapper for SSE connections"
```

---

### Task 2: 后端服务同步 API 改造

**Files:**
- Modify: `backend/app/api/services.py`

- [ ] **Step 1: 增加拉取并保存工具的逻辑函数**

修改 `backend/app/api/services.py`，导入 `sync_tools`。

```python
# Insert at the top of backend/app/api/services.py
from app.core.mcp_client import sync_tools
import json
import uuid
```

- [ ] **Step 2: 新增手动触发同步的 Endpoint**

```python
# Add endpoint in backend/app/api/services.py
@router.post("/{service_id}/sync-tools")
async def sync_service_tools(service_id: str):
    conn = get_db_connection()
    service = conn.execute("SELECT id, address FROM services WHERE id = ?", (service_id,)).fetchone()
    if not service:
        conn.close()
        raise HTTPException(status_code=404, detail="Service not found")
        
    tools_list = await sync_tools(service["address"])
    if not tools_list:
        conn.close()
        return {"status": "failed", "message": "No tools found or connection failed"}
        
    # Delete existing tools
    conn.execute("DELETE FROM tools WHERE service_id = ?", (service_id,))
    
    # Insert new tools
    for t in tools_list:
        conn.execute(
            """INSERT INTO tools (id, service_id, name, description, parameters_schema, enabled) 
               VALUES (?, ?, ?, ?, ?, 1)""",
            (str(uuid.uuid4()), service_id, t["name"], t.get("description", ""), json.dumps(t.get("inputSchema", {})))
        )
    
    # Update count
    tool_count = len(tools_list)
    conn.execute("UPDATE services SET tool_count = ? WHERE id = ?", (tool_count, service_id))
    conn.commit()
    conn.close()
    
    return {"status": "success", "tool_count": tool_count}
```

- [ ] **Step 3: 改造现有 Create Service 接口**

在 `create_service` 结尾 `conn.commit()` 之前调用同步：

```python
# Modify inside create_service in backend/app/api/services.py
# After INSERT INTO services...
# Don't await in sync route, so we use asyncio.run or await if it's async def
# WAIT, create_service is currently defined as async def create_service(...)
# Add the following before conn.commit() in create_service:

    tools_list = await sync_tools(service.address)
    tool_count = len(tools_list)
    if tool_count > 0:
        for t in tools_list:
            conn.execute(
                """INSERT INTO tools (id, service_id, name, description, parameters_schema, enabled) 
                   VALUES (?, ?, ?, ?, ?, 1)""",
                (str(uuid.uuid4()), new_id, t["name"], t.get("description", ""), json.dumps(t.get("inputSchema", {})))
            )
        conn.execute("UPDATE services SET tool_count = ? WHERE id = ?", (tool_count, new_id))
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/services.py
git commit -m "feat: add service tools sync via mcp protocol"
```

---

### Task 3: 后端 Agent 真实调用路由

**Files:**
- Modify: `backend/app/core/agent.py`

- [ ] **Step 1: 导入 mcp_client 及数据库查询辅助**

```python
# Top of backend/app/core/agent.py
import time
from app.core.mcp_client import execute_tool
from app.models.database import get_db_connection
```

- [ ] **Step 2: 改造工具执行拦截循环**

找到 `ChatAgent.stream_chat` 中的 `# Execute the tool call` Mock 部分，将其替换为真正的数据库查询与网络执行。

```python
# Replace the tool call execution section in ChatAgent.stream_chat:

                    if tool_call_name:
                        # 1. Lookup service address from DB
                        conn = get_db_connection()
                        # Get service_id from tools table using tool_name
                        tool_row = conn.execute("SELECT id, service_id FROM tools WHERE name = ? AND service_id = ?", (tool_call_name, service_id)).fetchone()
                        
                        if tool_row:
                            service_row = conn.execute("SELECT address FROM services WHERE id = ?", (tool_row["service_id"],)).fetchone()
                            service_url = service_row["address"] if service_row else None
                        else:
                            service_url = None
                            
                        # 2. Execute via MCP Client
                        start_time = time.time()
                        if service_url:
                            exec_result = await execute_tool(service_url, tool_call_name, tool_call_args)
                            result_data = exec_result.get("content", exec_result) if exec_result.get("status") == "success" else exec_result
                        else:
                            result_data = {"error": f"Tool {tool_call_name} not found or no service attached."}
                        
                        duration_ms = int((time.time() - start_time) * 1000)
                        
                        # 3. Update call_count
                        if tool_row and service_url and exec_result.get("status") == "success":
                            conn.execute("UPDATE tools SET call_count = call_count + 1 WHERE id = ?", (tool_row["id"],))
                            conn.commit()
                        conn.close()

                        yield f"data: {json.dumps({'id': tool_call_id, 'result': result_data, 'status': 'completed', 'duration_ms': duration_ms})}\n\n"
                        
                        # 4. Append to messages for LLM continue
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": json.dumps(result_data)
                        })
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/core/agent.py
git commit -m "feat: dynamically route llm tool calls to actual mcp services"
```

---

### Task 4: 前端增加同步按钮交互

**Files:**
- Modify: `frontend/src/services/api.js`
- Modify: `frontend/src/pages/Services/ServiceDetail.jsx`
- Modify: `frontend/src/pages/Services/index.jsx`

- [ ] **Step 1: 增加前端 API 方法**

修改 `frontend/src/services/api.js`，在 `servicesAPI` 对象中增加：
```javascript
  syncTools: (id) => api.post(`/services/${id}/sync-tools`),
```

- [ ] **Step 2: 服务详情页增加按钮**

修改 `frontend/src/pages/Services/ServiceDetail.jsx`：
导入 `SyncOutlined, Button, Space`。
在 `Card` 的 `extra` 属性中添加按钮触发同步。

```jsx
// frontend/src/pages/Services/ServiceDetail.jsx
import { SyncOutlined } from '@ant-design/icons';
// Add function:
  const onSyncTools = async () => {
    try {
      setLoading(true);
      await servicesAPI.syncTools(id);
      message.success('同步成功');
      fetchDetail();
    } catch (e) {
      message.error('同步失败');
      setLoading(false);
    }
  };

// Add to Card title="服务详情":
// <Card title="服务详情" extra={<Button type="primary" icon={<SyncOutlined />} onClick={onSyncTools}>同步工具</Button>} ...>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/services/api.js frontend/src/pages/Services/ServiceDetail.jsx
git commit -m "feat: add sync tools button to frontend UI"
```

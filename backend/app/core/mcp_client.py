import httpx
from httpx_sse import aconnect_sse
import json
import asyncio
from typing import List, Dict, Any

async def _mcp_rpc_call(service_url: str, method: str, params: dict = None) -> Any:
    """Helper to establish an SSE connection and send a JSON-RPC request."""
    sse_url = service_url if service_url.endswith("/sse") else f"{service_url.rstrip('/')}/sse"
    post_url = None
    
    timeout = httpx.Timeout(10.0, read=30.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        # We need to maintain the SSE connection while doing the POST
        # For simplicity in this short-lived model, we'll connect, get the endpoint, 
        # send the POST, and read the corresponding response event.
        
        async with aconnect_sse(client, "GET", sse_url) as event_source:
            # 1. Wait for endpoint event
            async for event in event_source.aiter_sse():
                if event.event == "endpoint":
                    # the data contains the URI to POST to (can be relative or absolute)
                    post_endpoint = event.data
                    if post_endpoint.startswith("http"):
                        post_url = post_endpoint
                    else:
                        base_url = sse_url.rsplit("/", 1)[0]
                        post_url = f"{base_url}{post_endpoint}"
                    break
            
            if not post_url:
                raise Exception("Did not receive endpoint event from SSE server")
            
            # 2. Send the JSON-RPC request
            request_id = "1"
            payload = {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
                "params": params or {}
            }
            post_resp = await client.post(post_url, json=payload)
            post_resp.raise_for_status()
            
            # 3. Wait for the result event on the SSE stream
            async for event in event_source.aiter_sse():
                if event.event == "message":
                    try:
                        data = json.loads(event.data)
                        if data.get("id") == request_id:
                            if "error" in data:
                                raise Exception(data["error"])
                            return data.get("result")
                    except json.JSONDecodeError:
                        pass

async def sync_tools(service_url: str) -> List[Dict]:
    """Connect to MCP service via SSE and list tools."""
    try:
        # First we must initialize the session according to MCP protocol
        # Note: A real MCP server requires 'initialize' before 'tools/list'.
        # Since we use short-lived connections, we do a quick init, then list.
        # But for brevity, if the server requires it, we must do it.
        # Let's write a quick initialization flow.
        
        service_url = service_url.strip()
        sse_url = service_url if service_url.endswith("/sse") else f"{service_url.rstrip('/')}/sse"
        post_url = None
        
        timeout = httpx.Timeout(10.0, read=30.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with aconnect_sse(client, "GET", sse_url) as event_source:
                iterator = event_source.aiter_sse().__aiter__()
                
                async for event in iterator:
                    if event.event == "endpoint":
                        post_endpoint = event.data
                        if post_endpoint.startswith("http"):
                            post_url = post_endpoint
                        else:
                            base_url = sse_url.rsplit("/", 1)[0]
                            post_url = f"{base_url}{post_endpoint}"
                        break
                
                if not post_url:
                    raise Exception("No endpoint event")
                
                # Send initialize
                init_payload = {
                    "jsonrpc": "2.0",
                    "id": "1",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "ai-mcp-gateway", "version": "1.0.0"}
                    }
                }
                await client.post(post_url, json=init_payload)
                
                # Wait for init response
                async for event in iterator:
                    if event.event == "message":
                        data = json.loads(event.data)
                        if data.get("id") == "1":
                            break
                
                # Send notifications/initialized
                await client.post(post_url, json={"jsonrpc": "2.0", "method": "notifications/initialized"})
                
                # Send tools/list
                await client.post(post_url, json={"jsonrpc": "2.0", "id": "2", "method": "tools/list"})
                
                async for event in iterator:
                    if event.event == "message":
                        data = json.loads(event.data)
                        if data.get("id") == "2":
                            tools_result = data.get("result", {}).get("tools", [])
                            
                            tools_list = []
                            for t in tools_result:
                                tools_list.append({
                                    "name": t.get("name"),
                                    "description": t.get("description", ""),
                                    "inputSchema": t.get("inputSchema", {})
                                })
                            return tools_list
                            
    except Exception as e:
        print(f"Failed to sync tools from {service_url}: {e}")
        return []

async def execute_tool(service_url: str, tool_name: str, arguments: dict) -> dict:
    """Connect to MCP service, call a tool, and close connection."""
    try:
        service_url = service_url.strip()
        sse_url = service_url if service_url.endswith("/sse") else f"{service_url.rstrip('/')}/sse"
        post_url = None
        
        timeout = httpx.Timeout(10.0, read=60.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with aconnect_sse(client, "GET", sse_url) as event_source:
                iterator = event_source.aiter_sse().__aiter__()
                async for event in iterator:
                    if event.event == "endpoint":
                        post_endpoint = event.data
                        if post_endpoint.startswith("http"):
                            post_url = post_endpoint
                        else:
                            base_url = sse_url.rsplit("/", 1)[0]
                            post_url = f"{base_url}{post_endpoint}"
                        break
                
                # Initialize
                init_payload = {
                    "jsonrpc": "2.0",
                    "id": "1",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "ai-mcp-gateway", "version": "1.0.0"}
                    }
                }
                await client.post(post_url, json=init_payload)
                
                async for event in iterator:
                    if event.event == "message":
                        data = json.loads(event.data)
                        if data.get("id") == "1":
                            break
                            
                await client.post(post_url, json={"jsonrpc": "2.0", "method": "notifications/initialized"})
                
                # Call tool
                call_payload = {
                    "jsonrpc": "2.0",
                    "id": "2",
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments
                    }
                }
                await client.post(post_url, json=call_payload)
                
                async for event in iterator:
                    if event.event == "message":
                        data = json.loads(event.data)
                        if data.get("id") == "2":
                            if "error" in data:
                                return {"status": "error", "error": str(data["error"])}
                            
                            result = data.get("result", {})
                            content = result.get("content", [])
                            return {"status": "success", "content": content}
                            
    except Exception as e:
        print(f"Failed to execute tool {tool_name} on {service_url}: {e}")
        return {"status": "error", "error": str(e)}

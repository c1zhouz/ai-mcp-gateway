import json
from typing import List, Dict, Any

import httpx
from httpx_sse import aconnect_sse

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

async def _sync_tools_or_raise(service_url: str) -> List[Dict]:
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
            init_response = await client.post(post_url, json=init_payload)
            init_response.raise_for_status()

            async for event in iterator:
                if event.event == "message":
                    data = json.loads(event.data)
                    if data.get("id") == "1":
                        if "error" in data:
                            raise Exception(data["error"])
                        break

            await client.post(post_url, json={"jsonrpc": "2.0", "method": "notifications/initialized"})

            tools_response = await client.post(
                post_url,
                json={"jsonrpc": "2.0", "id": "2", "method": "tools/list"},
            )
            tools_response.raise_for_status()

            async for event in iterator:
                if event.event == "message":
                    data = json.loads(event.data)
                    if data.get("id") == "2":
                        if "error" in data:
                            raise Exception(data["error"])
                        tools_result = data.get("result", {}).get("tools", [])
                        return [
                            {
                                "name": t.get("name"),
                                "description": t.get("description", ""),
                                "inputSchema": t.get("inputSchema", {})
                            }
                            for t in tools_result
                        ]
    return []


async def sync_tools(service_url: str) -> List[Dict]:
    """Connect to MCP service via SSE and list tools."""
    try:
        return await _sync_tools_or_raise(service_url)
    except Exception as e:
        print(f"Failed to sync tools from {service_url}: {e}")
        return []


async def check_service_health(service_url: str) -> Dict[str, Any]:
    try:
        tools = await _sync_tools_or_raise(service_url)
        return {"ok": True, "tools": tools}
    except Exception as e:
        return {"ok": False, "error": str(e)}

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

# Phase 4: MCP Protocol Implementation Design

## 1. Overview
The goal of Phase 4 is to implement real Model Context Protocol (MCP) communication between the AI Gateway and the registered microservices. The gateway will use the SSE (Server-Sent Events) over HTTP transport to dynamically discover tools from microservices and route LLM tool calls to them for execution.

## 2. Architecture & Transport
*   **Protocol Choice**: We will exclusively support the **SSE over HTTP** transport for MCP. This perfectly aligns with the gateway's distributed microservice architecture.
*   **Library**: We will utilize the official `mcp` Python SDK (or implement a lightweight standard JSON-RPC over SSE client) within the FastAPI backend to handle the underlying protocol complexities.

## 3. Component Details

### 3.1. MCP Client Wrapper (`backend/app/core/mcp_client.py`)
A new core utility will be created to manage MCP connections and operations:
*   `sync_tools(service_url: str) -> List[Dict]`: Connects to a service's `/sse` endpoint, issues a `tools/list` JSON-RPC request, parses the returned JSON Schema, and returns the list of available tools.
*   `execute_tool(service_url: str, tool_name: str, arguments: dict) -> dict`: Establishes a short-lived SSE connection to the service, issues a `tools/call` JSON-RPC request with the provided arguments, awaits the result, closes the connection, and returns the payload.

### 3.2. Tool Discovery & Synchronization (Option C)
*   **On-Creation Auto-Sync**: When a user adds a new microservice via `POST /api/services`, the backend will immediately call `sync_tools()` before returning the success response. The fetched tools will be inserted/upserted into the `tools` SQLite table, linking them to the newly created `service_id`.
*   **Manual Refresh API**: A new endpoint `POST /api/services/{id}/sync-tools` will be added. This allows the user to manually trigger a re-sync if the downstream microservice updates its tool definitions.
*   **Frontend Updates**: The Services page UI will be updated to trigger the sync on creation, and a "Sync Tools" button will be added to the service card or details view.

### 3.3. Tool Execution & Dynamic Routing (Option A)
*   **Short-Lived Connections**: To maintain simplicity and statelessness in the gateway, tool executions will use "short connections". For every tool call, a new SSE connection is established, the call is made, the result is fetched, and the connection is torn down.
*   **Chat Agent Updates (`backend/app/core/agent.py`)**:
    1.  When the LLM issues a tool call, the agent looks up the physical address (`service.address`) of the microservice via the `service_id`.
    2.  The agent pauses LLM generation, invoking `mcp_client.execute_tool()`.
    3.  Once the real result is retrieved, the gateway streams a `tool_result` event to the frontend (including latency metrics).
    4.  The result is appended to the conversation context, and the LLM is prompted to continue generating the final response.
*   **Analytics**: Upon successful execution, the gateway will increment the `call_count` for that specific tool in the database.

## 4. Error Handling
*   If a microservice is offline during `sync_tools`, the gateway will log an error but still allow the service to be created (with 0 tools initially), relying on manual sync later.
*   If a tool execution fails (e.g., service timeout, invalid arguments), the gateway will catch the exception and return a formatted error JSON to the LLM (e.g., `{"error": "Service unavailable or timeout"}`), allowing the LLM to gracefully handle the failure and inform the user.

## 5. Security & Constraints
*   The gateway assumes that internal microservice URLs are trusted. In a production environment, API key authentication might be required between the Gateway and the Microservice, but for Phase 4 MVP, we will rely on network-level trust.

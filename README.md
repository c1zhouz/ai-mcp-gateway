# AI MCP Gateway

一个面向企业 AI Agent 应用场景的 MCP 网关系统，为大语言模型提供标准化的工具调用能力接入层，支持 MCP 服务注册、心跳检测、API Key 鉴权路由、⼯具调用可视化与数据统计等 AI Infra 应用场景。

```text
AI Agent / Chat UI
  -> Gateway API
  -> API Key 鉴权 / 路由 / 工具发现 / 调用日志
  -> MCP Server
  -> 示例业务数据
```

## 项目亮点

- **MCP 服务注册与工具发现**：注册 MCP Server 后自动同步 `tools/list`，并展示工具 schema。
- **统一网关入口**：通过 `/gateway/{path}` 接收 JSON-RPC 请求，按路由规则转发到目标 MCP Server。
- **API Key 鉴权**：支持 Bearer Token 校验，API Key 哈希存储，按 `read` / `write` / `admin` 权限控制工具列表与调用。
- **Agent 对话测试台**：选择模型和 MCP 服务后，可以在聊天页观察工具调用参数、结果和最终回答。
- **可观测性原型**：提供请求统计、工具调用排行、服务状态、日志流和聊天会话历史。
- **安全收缩**：不提供在线写 Python 代码、写源码或重启服务入口，工具来源收敛为 MCP 服务发现与同步。
- **测试覆盖核心链路**：后端测试覆盖鉴权网关、路由调用、健康检查、危险部署入口移除和聊天会话持久化。

## 效果截图

### Agent 工具调用过程

![Agent 工具调用过程](docs/images/demo-chat-tool-calls.png)

### 拼团活动运营总结

![拼团活动运营总结](docs/images/demo-chat-summary.png)

## 技术栈

- Backend: FastAPI, aiosqlite, OpenAI-compatible API client, httpx, MCP Python SDK
- Frontend: React, Vite, Ant Design, Zustand, Axios
- Demo MCP Server: FastMCP, SQLAlchemy Async, MySQL
- Tests: Python `unittest`, HTTPX ASGI transport

## 目录结构

```text
.
├── backend/                 # FastAPI 后端与网关入口
│   ├── app/api/             # REST API、Gateway JSON-RPC 入口
│   ├── app/core/            # MCP client、Agent、鉴权、日志
│   ├── app/models/          # SQLite 初始化与 Pydantic 模型
│   └── tests/               # 后端核心链路测试
├── frontend/                # React 管理控制台
├── services/real_mall_mcp/  # 拼团商城 MCP Server
├── docs/demo.md             # 标准演示流程
└── docs/project-positioning.md
```

## 端口说明

| 服务 | 地址 |
|---|---|
| 前端控制台 | `http://localhost:3000` |
| 后端 REST API | `http://127.0.0.1:8000/api/...` |
| 网关 JSON-RPC 入口 | `http://127.0.0.1:8000/gateway/...` |
| 拼团商城 MCP 服务 | `http://127.0.0.1:5001/sse` |

> 当前没有单独监听 `8777` 的进程。旧设计里的 `8777` 已收敛为后端 `8000/gateway/...` 入口。

## 启动方式

### 1. 准备并启动拼团商城 MCP Server

```bash
cd /Users/yizhou/code/python_project/ai-mcp-gateway/services/real_mall_mcp
./venv/bin/python main.py
```

`real-mall-mcp` 只连接你已有的拼团商城 MySQL。确认 `.env` 类似：

```env
DATABASE_URL=mysql+aiomysql://root:123456@127.0.0.1:13306/group_buy_market
MCP_PORT=5001
```

如果 MySQL 没有启动或真实库没有数据，工具不会回退到本地演示库。

### 2. 启动后端

```bash
cd /Users/yizhou/code/python_project/ai-mcp-gateway
./venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

健康检查：

```bash
curl http://127.0.0.1:8000/api/health
```

### 3. 启动前端

```bash
cd /Users/yizhou/code/python_project/ai-mcp-gateway/frontend
npm run dev -- --host 127.0.0.1 --port 3000
```

访问：

```text
http://localhost:3000
```

## 标准演示流程

完整演示脚本见 [docs/demo.md](docs/demo.md)。

最短路径：

1. 在“微服务管理”添加 `http://127.0.0.1:5001`。
2. 执行健康检查或同步工具，确认工具列表出现。
3. 在“网关管理”创建 API Key，并配置路由规则，例如 `/mall/* -> real-mall-mcp`。
4. 使用 `/gateway/mall/tools` 调用 `tools/list` 或 `tools/call`。
5. 在“对话测试”填写 LLM API Key，选择服务，观察 Agent 对拼团活动、商品排行、未成团队伍等工具的调用过程。

## 验证命令

```bash
cd /Users/yizhou/code/python_project/ai-mcp-gateway
./venv/bin/python -m unittest discover backend/tests -v

cd services/real_mall_mcp
./venv/bin/python -m unittest discover tests -v

cd frontend
npm run lint
npm run build
```

当前 `npm run build` 可能出现 Vite 的大 chunk warning，这是前端包体积优化提醒，不影响功能运行。

更详细的定位与边界见 [docs/project-positioning.md](docs/project-positioning.md)。

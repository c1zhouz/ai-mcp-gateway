# AI MCP Gateway 管理控制台 — 设计规格书

## 1. 概述

### 1.1 项目目标

构建一个面向 AI Agent 的 MCP (Model Context Protocol) 网关系统管理控制台。该系统提供完整的网关管理能力，涵盖微服务注册、工具管理、对话测试等核心功能，帮助开发者管理和调试 AI Agent 与 MCP 工具的交互过程。

### 1.2 核心用户

- AI 应用开发者：需要管理 MCP 微服务和工具
- 运维人员：需要监控网关状态和系统健康
- 测试人员：需要通过对话界面调试 Agent 行为和工具调用

### 1.3 技术栈

| 层 | 技术 |
|---|---|
| 前端框架 | React 18 + Vite |
| UI 组件库 | Ant Design 5 |
| 状态管理 | Zustand |
| 数据请求 | Axios + React Query (TanStack Query) |
| 后端框架 | FastAPI (Python 3.11+) |
| LLM 集成 | OpenAI 兼容接口 |
| 流式通信 | SSE (Server-Sent Events) |
| 数据存储 | SQLite (开发阶段，可替换为 PostgreSQL) |

### 1.4 架构模式

**后端编排 + SSE 流式推送**：后端作为完整的 Agent 编排器，接收用户消息后执行完整的 Agent 循环（LLM 调用 → 工具执行 → 循环），通过 SSE 将中间过程（思考、工具调用、结果、最终回复）实时推送到前端。

---

## 2. 系统架构

```
┌────────────────────────────────────────────────────────────────┐
│            Frontend (React + Vite + Ant Design)                │
│                                                                │
│  ┌──────────┐ ┌──────────┐ ┌────────┐ ┌────────┐ ┌──────────┐│
│  │ Dashboard │ │ Gateway  │ │Services│ │ Tools  │ │   Chat   ││
│  └──────────┘ └──────────┘ └────────┘ └────────┘ └──────────┘│
│       │            │           │          │            │       │
│  ┌────┴────────────┴───────────┴──────────┴────────────┴────┐ │
│  │          API Service Layer (Axios + React Query)          │ │
│  └──────────────────────────┬────────────────────────────────┘ │
└─────────────────────────────┼──────────────────────────────────┘
                              │ REST API + SSE
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Backend (FastAPI + Python)                     │
│                                                                  │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌──────────────────┐│
│  │ REST API  │ │SSE Stream │ │  Agent    │ │ Gateway Config   ││
│  │ Endpoints │ │ Handler   │ │Orchestr.  │ │                  ││
│  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └──────────────────┘│
│        └──────────────┴─────────────┘                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Core: ServiceRegistry │ ToolManager │ LLMClient │MCPClient│  │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────┬─────────────────┬───────────────────────┘
                        │                 │
                        ▼                 ▼
              ┌──────────────┐  ┌──────────────────┐
              │ OpenAI-Compat│  │  MCP Services    │
              │ LLM Provider │  │ (Microservices)  │
              └──────────────┘  └──────────────────┘
```

---

## 3. 前端设计

### 3.1 整体布局

采用经典后台管理布局，与参考设计一致：

- **顶部导航栏 (64px)**：左侧 Logo "AI MCP Gateway"，右侧通知铃铛 + 用户头像 "管理员"
- **左侧菜单 (240px，可折叠至 80px)**：5 个菜单项，蓝色高亮当前页
- **右侧内容区**：各页面主内容，浅灰底色 (#f5f5f5)

### 3.2 页面设计

#### 3.2.1 首页 Dashboard

**统计卡片区（顶部 4 列）**：
- 在线微服务数（绿色图标）
- 注册工具总数（蓝色图标）
- 今日请求量（橙色图标）
- 请求成功率（百分比，绿/红色）

**图表区（中部 2 列）**：
- 左：请求量趋势折线图（最近 7 天，按小时聚合），使用 @ant-design/charts
- 右：工具调用排行 Top 10 水平条形图

**动态区（底部 2 列）**：
- 左：最近操作日志（表格：时间、操作、对象、状态）
- 右：系统告警通知（列表：级别图标 + 内容 + 时间）

#### 3.2.2 网关管理

**Tab 页签结构**：

**Tab 1 — 基础配置**：
- 表单：网关名称、监听地址、端口、请求超时(ms)、最大并发数
- 保存按钮

**Tab 2 — API Key 管理**：
- 表格列：Key 名称、Key 值(脱敏)、权限范围(Tag)、创建时间、状态、操作(复制/吊销)
- 顶部操作栏：+ 创建 API Key 按钮
- 创建弹窗：名称、权限范围(多选：读取/写入/管理)、过期时间

**Tab 3 — 路由规则**：
- 表格列：路径模式、目标微服务、优先级、状态、操作(编辑/删除)
- 支持添加/编辑路由规则

**Tab 4 — 日志配置**：
- 日志级别下拉选择
- 日志保留天数
- 日志输出目标

#### 3.2.3 微服务管理

**主页面 — 服务列表**：
- 视图切换：卡片视图 / 表格视图
- 卡片视图：每个服务显示为卡片 — 名称、地址、状态指示灯(绿/红)、工具数量、描述摘要
- 表格视图：名称、地址、状态、工具数、最后心跳时间、操作
- 顶部操作栏：+ 添加微服务按钮、搜索框、状态筛选

**添加/编辑 — 抽屉表单 (Drawer)**：
- 字段：服务名称、连接地址 (URL)、描述、健康检查间隔(秒)、自动重连开关
- 保存后自动进行首次健康检查

**服务详情页**：
- 顶部：服务基础信息 + 状态 + 在线时长
- 中部：该服务挂载的工具列表（表格：工具名、描述、启用状态、参数数量）
- 底部：调用统计图表（最近 24h 调用量趋势）

#### 3.2.4 工具管理

**主页面 — 工具列表**：
- 按微服务分组的可折叠面板 (Collapse)
- 每组内的工具以表格展示：工具名称、描述、所属服务、参数数量、启用状态、操作
- 顶部：搜索框 + 微服务筛选下拉 + 状态筛选

**工具详情 — 抽屉 (Drawer)**：
- 基础信息：名称、描述、所属微服务
- 参数定义：JSON Schema 渲染为可读的参数表格（参数名、类型、必填、描述、默认值）
- 原始 Schema：可折叠的 JSON 代码块
- 返回值示例：JSON 代码块

#### 3.2.5 对话测试（核心模块，依据参考图设计）

**左侧配置面板 (320px, 可折叠)**：
- 配置区标题 "配置"
- 后端地址输入框（默认 `http://127.0.0.1:8777`）
- 网关 API Key 输入框（密码类型，带切换可见按钮）
- LLM API Key 输入框（密码类型，带切换可见按钮）
- 选择微服务下拉框
- 连接/断开按钮（红色断开状态显示 "✕ 断开连接"）
- 工具列表区：显示所选微服务名称 + 工具数量，工具名以彩色 Tag 展示（蓝色/绿色）

**右侧聊天区**：

**消息列表**：
- 用户消息：蓝色气泡，右对齐，带头像和时间戳
- AI 消息：左对齐，白色背景，带 AI 头像和时间戳
- AI 消息内可包含三种特殊内容块：

**1. 思考过程 (Chain of Thought)**：
- 蓝色左边框的可折叠区块
- 标题栏：📋 图标 + "思考过程" + 收起/展开按钮
- 展开后显示 AI 的推理过程文本（Markdown 渲染）
- 默认展开，用户可手动收起

**2. 工具调用卡片 (Tool Call)**：
- 卡片样式，带边框
- 标题栏：🔧 图标 + "工具调用" + 工具名称 + 状态标签（调用中=蓝色旋转，✅已完成=绿色，❌失败=红色）
- 参数区：标签 "参数:" + JSON 代码块（语法高亮，浅黄色背景）
- 结果区：标签 "结果:" + JSON 代码块（语法高亮，浅绿色背景）
- 调用中状态时结果区显示加载动画

**3. 最终回复文本**：
- 普通文本，支持 Markdown 渲染
- 流式逐字显示效果

**底部输入栏**：
- 输入框：placeholder "输入消息，按 Enter 发送..."
- 发送按钮：蓝色圆形，右侧
- 发送中状态禁用输入

---

## 4. 后端设计

### 4.1 API 端点

#### Dashboard
| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/dashboard/stats` | 统计数据（服务数、工具数、请求量、成功率） |
| GET | `/api/dashboard/trend` | 请求量趋势数据 |
| GET | `/api/dashboard/top-tools` | 工具调用排行 |
| GET | `/api/dashboard/activities` | 最近操作日志 |
| GET | `/api/dashboard/alerts` | 系统告警 |

#### Gateway
| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/gateway/config` | 获取网关配置 |
| PUT | `/api/gateway/config` | 更新网关配置 |
| GET | `/api/gateway/api-keys` | API Key 列表 |
| POST | `/api/gateway/api-keys` | 创建 API Key |
| DELETE | `/api/gateway/api-keys/{id}` | 吊销 API Key |
| GET | `/api/gateway/routes` | 路由规则列表 |
| POST | `/api/gateway/routes` | 创建路由规则 |
| PUT | `/api/gateway/routes/{id}` | 编辑路由规则 |
| DELETE | `/api/gateway/routes/{id}` | 删除路由规则 |

#### Services
| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/services` | 微服务列表 |
| POST | `/api/services` | 注册微服务 |
| GET | `/api/services/{id}` | 微服务详情 |
| PUT | `/api/services/{id}` | 编辑微服务 |
| DELETE | `/api/services/{id}` | 删除微服务 |
| GET | `/api/services/{id}/tools` | 获取服务下工具列表 |
| POST | `/api/services/{id}/health-check` | 触发健康检查 |

#### Tools
| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/tools` | 工具列表（支持 `?service_id=&search=&enabled=` 筛选） |
| GET | `/api/tools/{id}` | 工具详情（含参数 Schema） |
| PATCH | `/api/tools/{id}` | 更新工具状态（启用/禁用） |

#### Chat
| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/chat/send` | 发送消息，返回 SSE 事件流 |
| GET | `/api/chat/sessions` | 会话列表 |
| GET | `/api/chat/sessions/{id}/messages` | 会话消息历史 |
| DELETE | `/api/chat/sessions/{id}` | 删除会话 |

### 4.2 SSE 事件流协议

对话测试的核心通信机制。`POST /api/chat/send` 返回 `text/event-stream`：

```
请求体:
{
  "session_id": "optional-uuid",
  "message": "用户消息文本",
  "gateway_url": "http://127.0.0.1:8777",
  "gateway_api_key": "gw-xxx",
  "llm_api_key": "sk-xxx",
  "service_id": "service-uuid",
  "model": "gpt-4o"
}
```

**事件类型定义**：

| 事件 | 数据结构 | 说明 |
|------|----------|------|
| `thinking` | `{"content": "思考过程文本"}` | AI 的推理过程，前端渲染为可折叠区块 |
| `tool_call` | `{"id": "tc_1", "name": "get_sales_stats", "arguments": {...}, "status": "calling"}` | 工具调用开始，前端渲染卡片（加载态） |
| `tool_result` | `{"id": "tc_1", "name": "get_sales_stats", "result": {...}, "status": "completed", "duration_ms": 234}` | 工具执行结果，前端更新卡片 |
| `message` | `{"content": "文本片段", "delta": true}` | AI 最终回复，delta=true 表示增量文本 |
| `error` | `{"code": "TOOL_TIMEOUT", "message": "工具执行超时"}` | 错误事件 |
| `done` | `{"usage": {"prompt_tokens": 500, "completion_tokens": 300}}` | 流结束标志 |

### 4.3 数据模型

```python
class Service(BaseModel):
    id: str                      # UUID
    name: str                    # 服务名称
    address: str                 # 连接地址
    description: str             # 描述
    status: str                  # online / offline / error
    health_check_interval: int   # 健康检查间隔(秒)
    auto_reconnect: bool         # 自动重连
    tool_count: int              # 挂载工具数
    last_heartbeat: datetime     # 最后心跳
    created_at: datetime

class Tool(BaseModel):
    id: str                      # UUID
    service_id: str              # 所属微服务 ID
    name: str                    # 工具名称
    description: str             # 工具描述
    parameters_schema: dict      # JSON Schema 参数定义
    enabled: bool                # 是否启用
    call_count: int              # 累计调用次数

class GatewayConfig(BaseModel):
    name: str                    # 网关名称
    listen_address: str          # 监听地址
    port: int                    # 端口
    timeout_ms: int              # 请求超时
    max_concurrency: int         # 最大并发
    log_level: str               # 日志级别
    log_retention_days: int      # 日志保留天数

class ApiKey(BaseModel):
    id: str
    name: str                    # Key 名称
    key_value: str               # Key 值（存储时哈希，展示时脱敏）
    permissions: list[str]       # 权限列表 ["read", "write", "admin"]
    expires_at: datetime | None  # 过期时间
    status: str                  # active / revoked
    created_at: datetime

class RouteRule(BaseModel):
    id: str
    path_pattern: str            # 路径模式
    target_service_id: str       # 目标微服务
    priority: int                # 优先级
    enabled: bool

class ChatSession(BaseModel):
    id: str
    title: str                   # 会话标题（取首条消息摘要）
    service_id: str              # 使用的微服务
    message_count: int
    created_at: datetime
    updated_at: datetime

class ChatMessage(BaseModel):
    id: str
    session_id: str
    role: str                    # user / assistant
    content: str                 # 最终文本内容
    thinking: str | None         # 思考过程
    tool_calls: list[ToolCall]   # 工具调用列表
    timestamp: datetime

class ToolCall(BaseModel):
    id: str
    name: str                    # 工具名称
    arguments: dict              # 调用参数
    result: dict | None          # 返回结果
    status: str                  # calling / completed / failed
    duration_ms: int | None      # 执行耗时
```

### 4.4 Agent 编排器

后端核心组件，负责完整的 Agent 循环：

```
def agent_loop(user_message, tools, llm_client):
    messages = [system_prompt, user_message]

    while True:
        # 1. 调用 LLM
        response = llm_client.chat(messages, tools=tools, stream=True)

        # 2. 流式输出思考过程
        yield SSE("thinking", thinking_content)

        # 3. 检查是否有工具调用
        if response.tool_calls:
            for tool_call in response.tool_calls:
                # 3a. 通知前端工具调用开始
                yield SSE("tool_call", {name, args, status="calling"})

                # 3b. 通过 MCP 客户端执行工具
                result = mcp_client.execute(tool_call)

                # 3c. 通知前端工具执行结果
                yield SSE("tool_result", {name, result, status="completed"})

                # 3d. 将结果加入上下文
                messages.append(tool_result_message)

            # 继续循环让 LLM 处理工具结果
            continue

        # 4. 无工具调用，流式输出最终回复
        yield SSE("message", {content, delta=True})
        break

    yield SSE("done", {usage})
```

---

## 5. 项目结构

```
ai-mcp-gateway/
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Layout/
│   │   │   │   ├── AppLayout.jsx        # 整体布局框架
│   │   │   │   ├── Sidebar.jsx          # 左侧菜单
│   │   │   │   └── Header.jsx           # 顶部导航
│   │   │   ├── Chat/
│   │   │   │   ├── MessageBubble.jsx    # 消息气泡
│   │   │   │   ├── ThinkingBlock.jsx    # 思考过程折叠块
│   │   │   │   ├── ToolCallCard.jsx     # 工具调用卡片
│   │   │   │   └── ChatInput.jsx        # 底部输入栏
│   │   │   ├── JsonViewer.jsx           # JSON 格式化显示
│   │   │   └── StatCard.jsx             # 统计卡片
│   │   ├── pages/
│   │   │   ├── Dashboard/
│   │   │   │   └── index.jsx
│   │   │   ├── Gateway/
│   │   │   │   └── index.jsx
│   │   │   ├── Services/
│   │   │   │   ├── index.jsx            # 服务列表
│   │   │   │   └── ServiceDetail.jsx    # 服务详情
│   │   │   ├── Tools/
│   │   │   │   └── index.jsx
│   │   │   └── Chat/
│   │   │       └── index.jsx
│   │   ├── services/
│   │   │   └── api.js                   # Axios 实例 + 各模块 API
│   │   ├── hooks/
│   │   │   ├── useSSE.js                # SSE 连接管理
│   │   │   └── useChat.js               # 聊天状态管理
│   │   ├── stores/
│   │   │   └── chatStore.js             # Zustand 聊天状态
│   │   ├── App.jsx                      # 路由配置
│   │   ├── main.jsx                     # 入口
│   │   └── index.css                    # 全局样式
│   ├── package.json
│   └── vite.config.js
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── dashboard.py
│   │   │   ├── gateway.py
│   │   │   ├── services.py
│   │   │   ├── tools.py
│   │   │   └── chat.py
│   │   ├── core/
│   │   │   ├── agent.py                 # Agent 编排器
│   │   │   ├── llm_client.py            # OpenAI 兼容 LLM 客户端
│   │   │   └── mcp_client.py            # MCP 协议客户端
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── service.py
│   │   │   ├── tool.py
│   │   │   ├── gateway.py
│   │   │   ├── chat.py
│   │   │   └── database.py             # SQLite 初始化
│   │   ├── services/
│   │   │   ├── service_manager.py
│   │   │   ├── tool_manager.py
│   │   │   └── gateway_manager.py
│   │   └── main.py                      # FastAPI 应用入口
│   └── requirements.txt
│
├── docs/
│   └── superpowers/specs/
├── .gitignore
└── README.md
```

---

## 6. 关键交互流程

### 6.1 对话测试完整流程

1. 用户在配置面板填写后端地址、API Key，选择微服务
2. 点击"连接"，前端调用 `GET /api/services/{id}/tools` 拉取工具列表
3. 工具列表以彩色 Tag 展示在配置面板底部
4. 用户在输入框键入消息，按 Enter 发送
5. 前端调用 `POST /api/chat/send`，建立 SSE 连接
6. 后端启动 Agent 循环，按顺序推送事件
7. 前端实时渲染：思考过程（可折叠）→ 工具调用卡片（实时状态）→ 最终回复（流式）
8. 收到 `done` 事件，标记消息完成，重新启用输入框

### 6.2 微服务注册流程

1. 用户点击"添加微服务"
2. 在抽屉表单中填写服务名称、地址等信息
3. 提交后，后端通过 MCP 协议连接目标服务
4. 自动发现并注册该服务提供的所有工具
5. 开始定期健康检查

---

## 7. 设计决策记录

| 决策 | 选择 | 理由 |
|------|------|------|
| 前端框架 | React + Vite | 生态丰富，组件库匹配度高 |
| UI 组件库 | Ant Design 5 | 与参考设计风格最接近，企业级管理后台标准 |
| 后端框架 | FastAPI | 异步支持好，自带文档，适合网关场景 |
| 流式通信 | SSE | 单向推送足够，比 WebSocket 简单可靠 |
| 状态管理 | Zustand | 轻量，适合中等复杂度，比 Redux 样板代码少 |
| 数据库 | SQLite | 开发阶段足够，后续可平滑迁移 |
| LLM 接口 | OpenAI 兼容 | 事实标准，覆盖大多数模型服务商 |
| 架构模式 | 后端编排 | 安全性好，Agent 循环可控，前端只需渲染 |

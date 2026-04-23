# Phase 3: 前端页面完整实现

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现前端 5 个模块的完整页面，包括 Dashboard、网关管理、微服务管理、工具管理、对话测试。

**Architecture:** 使用 Ant Design 组件构建页面，Zustand 管理聊天状态，自定义 useSSE hook 处理流式通信。

**Tech Stack:** React 18, Ant Design 5, Zustand, react-markdown, @ant-design/charts

**Depends on:** Phase 1 + Phase 2 完成

---

### Task 1: Dashboard 首页

**Files:**
- Create: `frontend/src/pages/Dashboard/index.jsx`
- Create: `frontend/src/pages/Dashboard/Dashboard.css`

- [ ] **Step 1: 实现 Dashboard 页面**

使用 Ant Design 的 `Row`, `Col`, `Card`, `Statistic` 组件展示 4 个统计卡片。使用 `@ant-design/charts` 的 `Line` 和 `Bar` 组件展示趋势图和工具排行。底部使用 `Table` 展示最近活动和 `List` 展示告警。

关键组件结构：
```
Dashboard
├── StatCards (Row > Col*4 > Card > Statistic)
├── Charts (Row > Col*2 > Line图 + Bar图)
└── Activity (Row > Col*2 > Table + List)
```

数据通过 `dashboardAPI.getStats()` 等接口获取，页面加载时用 `useEffect` 拉取。

- [ ] **Step 2: 验证页面渲染**
- [ ] **Step 3: Commit**

---

### Task 2: 网关管理页面

**Files:**
- Create: `frontend/src/pages/Gateway/index.jsx`
- Create: `frontend/src/pages/Gateway/Gateway.css`

- [ ] **Step 1: 实现 Tabs 页面结构**

使用 Ant Design `Tabs` 组件包含 4 个标签页：

**Tab 1 - 基础配置**: `Form` 表单，字段：名称、监听地址、端口、超时、最大并发。`Form.useForm()` 管理表单状态，`onFinish` 调用 `gatewayAPI.updateConfig()`。

**Tab 2 - API Key 管理**: `Table` 展示 Key 列表。列：名称、Key 值(脱敏)、权限(Tag)、状态(Badge)、操作(Button)。顶部 `Button` 触发 `Modal` 表单创建新 Key。

**Tab 3 - 路由规则**: `Table` 展示路由列表。列：路径模式、目标服务(Select)、优先级、状态(Switch)、操作。`Modal` 表单添加/编辑路由。

**Tab 4 - 日志配置**: 简单 `Form` 表单：日志级别(Select)、保留天数(InputNumber)。

- [ ] **Step 2: 验证各 Tab 页功能**
- [ ] **Step 3: Commit**

---

### Task 3: 微服务管理页面

**Files:**
- Create: `frontend/src/pages/Services/index.jsx`
- Create: `frontend/src/pages/Services/ServiceDetail.jsx`
- Create: `frontend/src/pages/Services/Services.css`
- Modify: `frontend/src/App.jsx` (添加详情路由)

- [ ] **Step 1: 实现服务列表页**

顶部操作栏：`Button` 添加服务 + `Input.Search` 搜索 + `Select` 状态筛选。

卡片视图 (默认)：`Row > Col*3` 网格，每个 `Card` 显示：服务名(标题)、地址、状态指示灯(`Badge`)、工具数量(`Tag`)、描述。Card 底部操作：编辑、健康检查、删除。

`Drawer` 表单：添加/编辑服务，字段：名称、地址(URL)、描述(TextArea)、健康检查间隔(InputNumber)、自动重连(Switch)。

- [ ] **Step 2: 实现服务详情页**

路由：`/services/:id`。顶部 `Descriptions` 展示服务信息 + 状态。中部 `Table` 展示该服务的工具列表。底部预留统计图表区域。

- [ ] **Step 3: 添加详情页路由**

在 `App.jsx` 中添加 `<Route path="/services/:id" element={<ServiceDetail />} />`。

- [ ] **Step 4: 验证完整流程**
- [ ] **Step 5: Commit**

---

### Task 4: 工具管理页面

**Files:**
- Create: `frontend/src/pages/Tools/index.jsx`
- Create: `frontend/src/pages/Tools/Tools.css`

- [ ] **Step 1: 实现工具列表页**

顶部操作栏：`Input.Search` 搜索 + `Select` 服务筛选 + `Select` 状态筛选。

使用 `Collapse` 按微服务分组，每组内 `Table`，列：工具名、描述、参数数量、启用状态(Switch)、操作(查看详情)。

点击"查看详情"打开 `Drawer`：
- 基础信息：`Descriptions` 展示名称、描述、所属服务
- 参数定义：`Table` 渲染 JSON Schema（参数名、类型、必填、描述）
- 原始 Schema：`Collapse` 包裹的 JSON 代码块

- [ ] **Step 2: 验证功能**
- [ ] **Step 3: Commit**

---

### Task 5: 对话测试 - 聊天状态管理

**Files:**
- Create: `frontend/src/stores/chatStore.js`
- Create: `frontend/src/hooks/useSSE.js`

- [ ] **Step 1: 创建 Zustand 聊天 Store**

```javascript
// frontend/src/stores/chatStore.js
import { create } from 'zustand';

const useChatStore = create((set, get) => ({
  messages: [],
  isConnected: false,
  isSending: false,
  config: {
    gatewayUrl: 'http://127.0.0.1:8777',
    gatewayApiKey: '',
    llmApiKey: '',
    llmBaseUrl: '',
    serviceId: '',
    model: 'gpt-4o',
  },
  tools: [],

  setConfig: (key, value) => set((s) => ({ config: { ...s.config, [key]: value } })),
  setTools: (tools) => set({ tools }),
  setConnected: (v) => set({ isConnected: v }),
  setSending: (v) => set({ isSending: v }),

  addUserMessage: (content) => set((s) => ({
    messages: [...s.messages, {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    }],
  })),

  addAssistantMessage: () => {
    const id = Date.now().toString();
    set((s) => ({
      messages: [...s.messages, {
        id,
        role: 'assistant',
        content: '',
        thinking: null,
        toolCalls: [],
        timestamp: new Date().toISOString(),
      }],
    }));
    return id;
  },

  updateLastAssistant: (field, value) => set((s) => {
    const msgs = [...s.messages];
    const last = msgs.findLast((m) => m.role === 'assistant');
    if (last) last[field] = value;
    return { messages: msgs };
  }),

  appendToolCall: (tc) => set((s) => {
    const msgs = [...s.messages];
    const last = msgs.findLast((m) => m.role === 'assistant');
    if (last) last.toolCalls = [...last.toolCalls, tc];
    return { messages: msgs };
  }),

  updateToolCall: (tcId, updates) => set((s) => {
    const msgs = [...s.messages];
    const last = msgs.findLast((m) => m.role === 'assistant');
    if (last) {
      last.toolCalls = last.toolCalls.map((tc) =>
        tc.id === tcId ? { ...tc, ...updates } : tc
      );
    }
    return { messages: msgs };
  }),

  clearMessages: () => set({ messages: [] }),
}));

export default useChatStore;
```

- [ ] **Step 2: 创建 SSE Hook**

```javascript
// frontend/src/hooks/useSSE.js
import { useCallback } from 'react';
import useChatStore from '../stores/chatStore';

export default function useSSE() {
  const store = useChatStore();

  const sendMessage = useCallback(async (message) => {
    const { config } = useChatStore.getState();
    store.addUserMessage(message);
    store.setSending(true);
    const msgId = store.addAssistantMessage();

    try {
      const response = await fetch('/api/chat/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          gateway_url: config.gatewayUrl,
          gateway_api_key: config.gatewayApiKey,
          llm_api_key: config.llmApiKey,
          llm_base_url: config.llmBaseUrl || undefined,
          service_id: config.serviceId || undefined,
          model: config.model,
        }),
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        let eventType = '';
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            eventType = line.slice(7).trim();
          } else if (line.startsWith('data: ') && eventType) {
            const data = JSON.parse(line.slice(6));
            switch (eventType) {
              case 'thinking':
                store.updateLastAssistant('thinking', data.content);
                break;
              case 'tool_call':
                store.appendToolCall(data);
                break;
              case 'tool_result':
                store.updateToolCall(data.id, { result: data.result, status: data.status, duration_ms: data.duration_ms });
                break;
              case 'message':
                store.updateLastAssistant('content', (useChatStore.getState().messages.findLast(m => m.role === 'assistant')?.content || '') + data.content);
                break;
              case 'error':
                store.updateLastAssistant('content', `❌ Error: ${data.message}`);
                break;
              case 'done':
                break;
            }
            eventType = '';
          }
        }
      }
    } catch (err) {
      store.updateLastAssistant('content', `❌ 请求失败: ${err.message}`);
    } finally {
      store.setSending(false);
    }
  }, []);

  return { sendMessage };
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/stores/ frontend/src/hooks/
git commit -m "feat: add chat store and SSE hook"
```

---

### Task 6: 对话测试 - 聊天组件

**Files:**
- Create: `frontend/src/components/Chat/ThinkingBlock.jsx`
- Create: `frontend/src/components/Chat/ToolCallCard.jsx`
- Create: `frontend/src/components/Chat/MessageBubble.jsx`
- Create: `frontend/src/components/Chat/ChatInput.jsx`
- Create: `frontend/src/components/Chat/Chat.css`

- [ ] **Step 1: 实现 ThinkingBlock 组件**

可折叠区块，蓝色左边框。使用 `useState` 控制展开/收起。标题："📋 思考过程" + 收起/展开按钮。内容使用 `react-markdown` 渲染。

- [ ] **Step 2: 实现 ToolCallCard 组件**

卡片样式。标题栏：🔧 + "工具调用" + 工具名 `Tag` + 状态标签。参数区 + 结果区用 `pre > code` 展示格式化 JSON，参数背景浅黄色，结果背景浅绿色。调用中状态显示 `Spin`。

- [ ] **Step 3: 实现 MessageBubble 组件**

根据 `role` 渲染不同样式。用户消息：蓝色气泡右对齐。AI 消息：左对齐，包含可选的 ThinkingBlock + ToolCallCard[] + 文本内容。

- [ ] **Step 4: 实现 ChatInput 组件**

`Input` + 发送 `Button`。Enter 发送，Shift+Enter 换行。发送中禁用。

- [ ] **Step 5: Commit**

---

### Task 7: 对话测试 - 完整页面组装

**Files:**
- Modify: `frontend/src/pages/Chat/index.jsx`
- Create: `frontend/src/pages/Chat/Chat.css`

- [ ] **Step 1: 实现 Chat 页面**

左侧配置面板 (320px)：
- 后端地址 Input
- 网关 API Key Input.Password
- LLM API Key Input.Password
- 微服务 Select (从 servicesAPI 拉取)
- 连接/断开 Button
- 工具列表 Tag 展示

右侧聊天区：
- 消息列表 (MessageBubble[]) 使用 ref 自动滚动到底部
- 底部 ChatInput

状态来自 `useChatStore`，发送消息用 `useSSE().sendMessage`。

- [ ] **Step 2: 端到端验证**

启动前后端，打开对话测试页面，配置 LLM API Key，发送消息验证 SSE 流式响应。

- [ ] **Step 3: Commit**

```bash
git add frontend/
git commit -m "feat: implement chat test page with SSE streaming"
```

---

### Task 8: 样式打磨与视觉还原

**Files:**
- Modify: 各组件 CSS 文件

- [ ] **Step 1: 对照参考图微调样式**

重点还原：
- 侧边栏选中项蓝色高亮
- 工具调用卡片的渐变边框和状态标签颜色
- 思考过程区块的蓝色左边框
- 用户消息气泡的蓝色圆角样式
- 配置面板的整体布局与间距
- 工具 Tag 的颜色方案（蓝色/绿色交替）

- [ ] **Step 2: 全局视觉检查**
- [ ] **Step 3: Final Commit**

```bash
git add .
git commit -m "feat: polish UI styles to match reference design"
```

---

## Phase 3 完成标准

- [x] Dashboard 首页展示统计数据和图表
- [x] 网关管理 4 个 Tab 页功能完整
- [x] 微服务管理 CRUD + 详情页
- [x] 工具管理列表 + 详情 + 搜索筛选
- [x] 对话测试完整功能：配置 + 工具列表 + 聊天 + 思考过程 + 工具调用卡片
- [x] 视觉风格与参考图一致

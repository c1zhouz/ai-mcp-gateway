# Phase 1: 项目基础架构搭建

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 搭建 AI MCP Gateway 管理控制台的前后端项目基础架构，包含完整的布局框架和路由系统。

**Architecture:** 前端 React+Vite+AntDesign 提供 SPA 管理界面，后端 FastAPI 提供 REST API。前端通过 Axios 调用后端，对话测试模块通过 SSE 实现流式通信。

**Tech Stack:** React 18, Vite, Ant Design 5, Zustand, Axios, FastAPI, SQLite, Python 3.11+

**Spec:** `docs/superpowers/specs/2026-04-23-mcp-gateway-console-design.md`

---

### Task 1: 初始化前端项目

**Files:**
- Create: `frontend/` (via Vite scaffold)
- Modify: `frontend/package.json`
- Modify: `frontend/vite.config.js`

- [ ] **Step 1: 用 Vite 创建 React 项目**

```bash
cd /Users/yizhou/code/python_project/ai-mcp-gateway
npx -y create-vite@latest frontend --template react
```

- [ ] **Step 2: 安装依赖**

```bash
cd /Users/yizhou/code/python_project/ai-mcp-gateway/frontend
npm install antd @ant-design/icons @ant-design/charts react-router-dom zustand axios react-markdown
```

- [ ] **Step 3: 配置 Vite 代理**

修改 `frontend/vite.config.js`:

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

- [ ] **Step 4: 验证前端启动**

```bash
cd /Users/yizhou/code/python_project/ai-mcp-gateway/frontend
npm run dev
```
Expected: 浏览器访问 http://localhost:3000 看到 Vite 默认页面

- [ ] **Step 5: Commit**

```bash
git add frontend/
git commit -m "feat: initialize frontend project with React + Vite"
```

---

### Task 2: 初始化后端项目

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/main.py`
- Create: `backend/app/__init__.py`
- Create: `backend/app/api/__init__.py`

- [ ] **Step 1: 创建后端目录结构**

```bash
mkdir -p backend/app/api backend/app/core backend/app/models backend/app/services
touch backend/app/__init__.py backend/app/api/__init__.py backend/app/core/__init__.py backend/app/models/__init__.py backend/app/services/__init__.py
```

- [ ] **Step 2: 创建 requirements.txt**

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
pydantic==2.9.0
openai==1.50.0
httpx==0.27.0
python-dotenv==1.0.1
aiosqlite==0.20.0
```

- [ ] **Step 3: 安装 Python 依赖**

```bash
cd /Users/yizhou/code/python_project/ai-mcp-gateway
source venv/bin/activate
pip install -r backend/requirements.txt
```

- [ ] **Step 4: 创建 FastAPI 入口 `backend/app/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI MCP Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
```

- [ ] **Step 5: 验证后端启动**

```bash
cd /Users/yizhou/code/python_project/ai-mcp-gateway
source venv/bin/activate
uvicorn backend.app.main:app --reload --port 8000
```
Expected: 访问 http://localhost:8000/api/health 返回 `{"status":"ok"}`

- [ ] **Step 6: Commit**

```bash
git add backend/
git commit -m "feat: initialize backend project with FastAPI"
```

---

### Task 3: 前端布局框架 - AppLayout

**Files:**
- Create: `frontend/src/components/Layout/AppLayout.jsx`
- Create: `frontend/src/components/Layout/AppLayout.css`

- [ ] **Step 1: 创建 AppLayout 组件**

```jsx
// frontend/src/components/Layout/AppLayout.jsx
import React, { useState } from 'react';
import { Layout, Menu, Avatar, Dropdown, Badge, Space } from 'antd';
import {
  HomeOutlined,
  ApiOutlined,
  CloudServerOutlined,
  ToolOutlined,
  MessageOutlined,
  BellOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import './AppLayout.css';

const { Header, Sider, Content } = Layout;

const menuItems = [
  { key: '/', icon: <HomeOutlined />, label: '首页' },
  { key: '/gateway', icon: <ApiOutlined />, label: '网关管理' },
  { key: '/services', icon: <CloudServerOutlined />, label: '微服务管理' },
  { key: '/tools', icon: <ToolOutlined />, label: '工具管理' },
  { key: '/chat', icon: <MessageOutlined />, label: '对话测试' },
];

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const selectedKey = menuItems
    .map((item) => item.key)
    .filter((key) => key !== '/')
    .find((key) => location.pathname.startsWith(key)) || '/';

  return (
    <Layout className="app-layout">
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        className="app-sider"
        width={240}
        collapsedWidth={80}
      >
        <div className="app-logo">
          <ApiOutlined className="logo-icon" />
          {!collapsed && <span className="logo-text">AI MCP Gateway</span>}
        </div>
        <Menu
          theme="light"
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header className="app-header">
          <span
            className="collapse-trigger"
            onClick={() => setCollapsed(!collapsed)}
          >
            {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          </span>
          <h2 className="page-title">
            {menuItems.find((item) => item.key === selectedKey)?.label || '首页'}
          </h2>
          <Space className="header-right" size={20}>
            <Badge count={3} size="small">
              <BellOutlined style={{ fontSize: 18 }} />
            </Badge>
            <Dropdown
              menu={{
                items: [
                  { key: 'profile', label: '个人设置' },
                  { key: 'logout', label: '退出登录' },
                ],
              }}
            >
              <Space style={{ cursor: 'pointer' }}>
                <Avatar style={{ backgroundColor: '#1677ff' }}>管</Avatar>
                <span>管理员</span>
              </Space>
            </Dropdown>
          </Space>
        </Header>
        <Content className="app-content">
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
```

- [ ] **Step 2: 创建布局样式**

```css
/* frontend/src/components/Layout/AppLayout.css */
.app-layout {
  min-height: 100vh;
}

.app-sider {
  background: #fff !important;
  border-right: 1px solid #f0f0f0;
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  z-index: 10;
}

.app-sider .ant-menu {
  border-inline-end: none !important;
}

.app-logo {
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 24px;
  gap: 10px;
  border-bottom: 1px solid #f0f0f0;
}

.logo-icon {
  font-size: 24px;
  color: #1677ff;
}

.logo-text {
  font-size: 16px;
  font-weight: 600;
  color: #1d1d1f;
  white-space: nowrap;
}

.app-header {
  background: #fff !important;
  padding: 0 24px !important;
  display: flex;
  align-items: center;
  border-bottom: 1px solid #f0f0f0;
  position: sticky;
  top: 0;
  z-index: 9;
  height: 64px;
}

.collapse-trigger {
  font-size: 18px;
  cursor: pointer;
  margin-right: 16px;
  color: #666;
}

.page-title {
  flex: 1;
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.header-right {
  margin-left: auto;
}

.app-content {
  margin: 24px;
  min-height: calc(100vh - 64px - 48px);
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/
git commit -m "feat: add AppLayout with sidebar and header"
```

---

### Task 4: 路由配置与占位页面

**Files:**
- Create: `frontend/src/pages/Dashboard/index.jsx`
- Create: `frontend/src/pages/Gateway/index.jsx`
- Create: `frontend/src/pages/Services/index.jsx`
- Create: `frontend/src/pages/Tools/index.jsx`
- Create: `frontend/src/pages/Chat/index.jsx`
- Modify: `frontend/src/App.jsx`
- Modify: `frontend/src/main.jsx`
- Modify: `frontend/src/index.css`

- [ ] **Step 1: 创建 5 个占位页面**

每个页面文件使用相同模式，以 Dashboard 为例：

```jsx
// frontend/src/pages/Dashboard/index.jsx
import React from 'react';

export default function Dashboard() {
  return <div><h3>首页 Dashboard</h3><p>开发中...</p></div>;
}
```

同理创建 `Gateway/index.jsx`、`Services/index.jsx`、`Tools/index.jsx`、`Chat/index.jsx`，分别显示对应模块名称。

- [ ] **Step 2: 配置路由 App.jsx**

```jsx
// frontend/src/App.jsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import AppLayout from './components/Layout/AppLayout';
import Dashboard from './pages/Dashboard';
import Gateway from './pages/Gateway';
import Services from './pages/Services';
import Tools from './pages/Tools';
import Chat from './pages/Chat';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/gateway" element={<Gateway />} />
          <Route path="/services" element={<Services />} />
          <Route path="/tools" element={<Tools />} />
          <Route path="/chat" element={<Chat />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
```

- [ ] **Step 3: 更新 main.jsx 入口**

```jsx
// frontend/src/main.jsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ConfigProvider locale={zhCN}>
      <App />
    </ConfigProvider>
  </React.StrictMode>
);
```

- [ ] **Step 4: 更新全局样式 index.css**

```css
/* frontend/src/index.css */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
}

/* Sider offset for fixed sidebar */
.ant-layout > .ant-layout {
  margin-left: 240px;
  transition: margin-left 0.2s;
}

.ant-layout-sider-collapsed + .ant-layout {
  margin-left: 80px;
}
```

- [ ] **Step 5: 验证完整布局**

```bash
cd /Users/yizhou/code/python_project/ai-mcp-gateway/frontend
npm run dev
```
Expected: 打开 http://localhost:3000，看到左侧菜单 + 顶部导航 + 右侧内容区，点击各菜单项可切换页面。

- [ ] **Step 6: Commit**

```bash
git add frontend/
git commit -m "feat: add routing and placeholder pages for all modules"
```

---

### Task 5: 后端数据库初始化与基础模型

**Files:**
- Create: `backend/app/models/database.py`
- Create: `backend/app/models/service.py`
- Create: `backend/app/models/tool.py`
- Create: `backend/app/models/gateway.py`
- Create: `backend/app/models/chat.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: 创建数据库初始化模块**

```python
# backend/app/models/database.py
import aiosqlite
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "gateway.db")


async def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    db = await get_db()
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS services (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            description TEXT DEFAULT '',
            status TEXT DEFAULT 'offline',
            health_check_interval INTEGER DEFAULT 30,
            auto_reconnect INTEGER DEFAULT 1,
            tool_count INTEGER DEFAULT 0,
            last_heartbeat TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS tools (
            id TEXT PRIMARY KEY,
            service_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            parameters_schema TEXT DEFAULT '{}',
            enabled INTEGER DEFAULT 1,
            call_count INTEGER DEFAULT 0,
            FOREIGN KEY (service_id) REFERENCES services(id)
        );

        CREATE TABLE IF NOT EXISTS gateway_config (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            name TEXT DEFAULT 'AI MCP Gateway',
            listen_address TEXT DEFAULT '0.0.0.0',
            port INTEGER DEFAULT 8000,
            timeout_ms INTEGER DEFAULT 30000,
            max_concurrency INTEGER DEFAULT 100,
            log_level TEXT DEFAULT 'INFO',
            log_retention_days INTEGER DEFAULT 7
        );

        CREATE TABLE IF NOT EXISTS api_keys (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            key_value TEXT NOT NULL,
            permissions TEXT DEFAULT '["read"]',
            expires_at TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS route_rules (
            id TEXT PRIMARY KEY,
            path_pattern TEXT NOT NULL,
            target_service_id TEXT NOT NULL,
            priority INTEGER DEFAULT 0,
            enabled INTEGER DEFAULT 1,
            FOREIGN KEY (target_service_id) REFERENCES services(id)
        );

        CREATE TABLE IF NOT EXISTS chat_sessions (
            id TEXT PRIMARY KEY,
            title TEXT DEFAULT '',
            service_id TEXT,
            message_count INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS chat_messages (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT DEFAULT '',
            thinking TEXT,
            tool_calls TEXT DEFAULT '[]',
            timestamp TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
        );

        INSERT OR IGNORE INTO gateway_config (id) VALUES (1);
    """)
    await db.commit()
    await db.close()
```

- [ ] **Step 2: 创建 Pydantic 模型文件**

```python
# backend/app/models/service.py
from pydantic import BaseModel
from datetime import datetime


class ServiceCreate(BaseModel):
    name: str
    address: str
    description: str = ""
    health_check_interval: int = 30
    auto_reconnect: bool = True


class ServiceUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    description: str | None = None
    health_check_interval: int | None = None
    auto_reconnect: bool | None = None


class ServiceResponse(BaseModel):
    id: str
    name: str
    address: str
    description: str
    status: str
    health_check_interval: int
    auto_reconnect: bool
    tool_count: int
    last_heartbeat: str | None
    created_at: str
```

同理创建 `tool.py`、`gateway.py`、`chat.py` 的 Pydantic 模型（Create/Update/Response 模式）。

- [ ] **Step 3: 在 main.py 中添加数据库初始化**

在 `backend/app/main.py` 添加：

```python
from contextlib import asynccontextmanager
from backend.app.models.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="AI MCP Gateway", version="1.0.0", lifespan=lifespan)
```

- [ ] **Step 4: 验证数据库初始化**

```bash
cd /Users/yizhou/code/python_project/ai-mcp-gateway
source venv/bin/activate
uvicorn backend.app.main:app --reload --port 8000
```
Expected: 启动后 `backend/data/gateway.db` 文件被创建

- [ ] **Step 5: Commit**

```bash
git add backend/
git commit -m "feat: add database schema and Pydantic models"
```

---

### Task 6: 前端 API 服务层

**Files:**
- Create: `frontend/src/services/api.js`

- [ ] **Step 1: 创建 Axios 实例和 API 模块**

```javascript
// frontend/src/services/api.js
import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// Dashboard
export const dashboardAPI = {
  getStats: () => api.get('/dashboard/stats'),
  getTrend: () => api.get('/dashboard/trend'),
  getTopTools: () => api.get('/dashboard/top-tools'),
  getActivities: () => api.get('/dashboard/activities'),
};

// Gateway
export const gatewayAPI = {
  getConfig: () => api.get('/gateway/config'),
  updateConfig: (data) => api.put('/gateway/config', data),
  getApiKeys: () => api.get('/gateway/api-keys'),
  createApiKey: (data) => api.post('/gateway/api-keys', data),
  deleteApiKey: (id) => api.delete(`/gateway/api-keys/${id}`),
  getRoutes: () => api.get('/gateway/routes'),
  createRoute: (data) => api.post('/gateway/routes', data),
  updateRoute: (id, data) => api.put(`/gateway/routes/${id}`, data),
  deleteRoute: (id) => api.delete(`/gateway/routes/${id}`),
};

// Services
export const servicesAPI = {
  list: () => api.get('/services'),
  get: (id) => api.get(`/services/${id}`),
  create: (data) => api.post('/services', data),
  update: (id, data) => api.put(`/services/${id}`, data),
  delete: (id) => api.delete(`/services/${id}`),
  getTools: (id) => api.get(`/services/${id}/tools`),
  healthCheck: (id) => api.post(`/services/${id}/health-check`),
};

// Tools
export const toolsAPI = {
  list: (params) => api.get('/tools', { params }),
  get: (id) => api.get(`/tools/${id}`),
  updateStatus: (id, enabled) => api.patch(`/tools/${id}`, { enabled }),
};

// Chat
export const chatAPI = {
  getSessions: () => api.get('/chat/sessions'),
  getMessages: (sessionId) => api.get(`/chat/sessions/${sessionId}/messages`),
  deleteSession: (sessionId) => api.delete(`/chat/sessions/${sessionId}`),
};

export default api;
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/services/
git commit -m "feat: add frontend API service layer"
```

---

## Phase 1 完成标准

- [x] 前端项目初始化（React + Vite + Ant Design）
- [x] 后端项目初始化（FastAPI + SQLite）
- [x] 完整的侧边栏 + 顶部导航布局
- [x] 5 个页面的路由配置
- [x] 数据库 Schema 和 Pydantic 模型
- [x] 前端 API 服务层

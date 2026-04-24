# Phase 6: 实时日志对接与全局 UI 抛光 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现真实的网关业务日志实时推送，并统一全站 UI 风格为“毛玻璃+渐变”的 Premium 质感。

**Architecture:** 后端使用全局异步队列（asyncio.Queue）捕获业务事件，通过 SSE 协议推送到前端；前端使用自定义 Hook 订阅日志流并在控制台展示。全站 CSS 引入统一的设计令牌。

**Tech Stack:** FastAPI, SSE, React, Ant Design 5, CSS Variables.

---

### Task 1: 后端日志管理核心

**Files:**
- Create: `backend/app/core/logger.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: 创建 LogManager 单例**
```python
import asyncio
from datetime import datetime
from collections import deque

class LogManager:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.queue = asyncio.Queue()
            cls._instance.history = deque(maxlen=50)
        return cls._instance

    async def log(self, message: str, level: str = "INFO"):
        log_entry = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": level,
            "message": message
        }
        self.history.append(log_entry)
        await self.queue.put(log_entry)

log_manager = LogManager()
```

- [ ] **Step 2: 在 main.py 中确保环境准备就绪**
- [ ] **Step 3: Commit**

---

### Task 2: 后端日志上报集成

**Files:**
- Modify: `backend/app/core/agent.py`
- Modify: `backend/app/services/service_manager.py`

- [ ] **Step 1: 在 Agent 循环中增加日志上报**
```python
from backend.app.core.logger import log_manager
# 在工具调用处增加
await log_manager.log(f"开始执行工具: {tool_name}", "TOOL")
# 在工具结束处增加
await log_manager.log(f"工具 {tool_name} 执行完毕，耗时 {duration}ms", "TOOL")
```

- [ ] **Step 2: 在 Service Manager 中增加健康检查日志**
```python
# 在状态切换处
await log_manager.log(f"微服务 [{service_name}] 状态切换为: {new_status}", "INFO")
```

- [ ] **Step 3: Commit**

---

### Task 3: 后端 SSE 日志端点

**Files:**
- Modify: `backend/app/api/gateway.py`

- [ ] **Step 1: 实现日志流端点**
```python
from backend.app.core.logger import log_manager

@router.get("/logs/stream")
async def stream_logs():
    async def event_generator():
        # 先发送历史记录
        for entry in log_manager.history:
            yield f"data: {json.dumps(entry)}\n\n"
        
        # 持续发送新日志
        while True:
            entry = await log_manager.queue.get()
            yield f"data: {json.dumps(entry)}\n\n"
            
    return EventSourceResponse(event_generator())
```

- [ ] **Step 2: Commit**

---

### Task 4: 前端日志订阅与 UI 美化 (Gateway)

**Files:**
- Create: `frontend/src/hooks/useLogStream.js`
- Modify: `frontend/src/pages/Gateway/index.jsx`
- Modify: `frontend/src/pages/Gateway/Gateway.css`

- [ ] **Step 1: 实现 useLogStream Hook**
- [ ] **Step 2: 在网关页面对接真实日志流**
- [ ] **Step 3: 应用毛玻璃和渐变样式到网关页面卡片**
- [ ] **Step 4: Commit**

---

### Task 5: 全局 UI 抛光 (Services & Tools)

**Files:**
- Modify: `frontend/src/pages/Services/Services.css`
- Modify: `frontend/src/pages/Tools/Tools.css`
- Modify: `frontend/src/index.css`

- [ ] **Step 1: 在 index.css 定义全局设计令牌**
```css
:root {
  --premium-gradient: linear-gradient(45deg, #1677ff, #722ed1);
  --glass-bg: rgba(255, 255, 255, 0.7);
  --glass-blur: blur(10px);
}
```

- [ ] **Step 2: 重构服务管理页面样式**
- [ ] **Step 3: 重构工具管理页面样式**
- [ ] **Step 4: Commit**

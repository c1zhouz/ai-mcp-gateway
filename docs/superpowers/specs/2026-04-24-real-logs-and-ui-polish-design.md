# Phase 6: 实时日志对接与全局 UI 抛光 — 设计规格书

## 1. 概述

本阶段是 AI MCP Gateway 项目的收尾阶段，重点在于提升系统的“生产就绪度”和“视觉一致性”。通过对接真实的业务日志流，用户可以实时监控网关与微服务之间的交互；通过全局 UI 抛光，确保所有功能模块都具备一致的高端视觉体验。

## 2. 核心功能设计

### 2.1 实时业务日志系统 (Real-time Business Logs)

#### 2.1.1 后端实现 (Python/FastAPI)
- **LogManager (单例)**:
    - 维护一个 `asyncio.Queue` (最大容量 1000 条)。
    - 提供 `log(message: str, level: str = "INFO")` 方法。
- **日志采集点**:
    - `backend/app/core/agent.py`: 工具调用开始、结束、报错。
    - `backend/app/services/service_manager.py`: 微服务心跳、状态切换。
    - `backend/app/api/chat.py`: 会话建立、鉴权结果。
- **SSE 端点**:
    - `GET /api/gateway/logs/stream`: 
        - 建立连接后，先推送 Queue 中已有的最近 50 条日志。
        - 随后进入监听模式，Queue 有新数据即 yield。

#### 2.1.2 前端实现 (React)
- **useLogStream Hook**:
    - 管理 SSE 连接，自动处理断线重连。
    - 将收到的日志片段追加到本地状态。
- **LogViewer 组件 (控制台样式)**:
    - 黑色背景 (#1e1e1e)，等宽字体。
    - 根据日志级别（INFO, WARN, ERROR, TOOL）渲染不同颜色。
    - 自动滚动到底部。

### 2.2 全局 UI 抛光 (Global UI Polish)

#### 2.2.1 风格统一定义
- **Glassmorphism**: 所有页面主容器/卡片采用 `backdrop-filter: blur(10px)`。
- **Gradients**: 核心交互按钮和强调数值采用 `linear-gradient(45deg, #1677ff, #722ed1)`。
- **Animations**: 增加页面切换的 `fadeIn` 效果。

#### 2.2.2 页面针对性美化
- **Services (微服务管理)**:
    - 状态灯增加呼吸灯动画效果。
    - 卡片视图增加 Hover 缩放效果。
- **Gateway (网关管理)**:
    - 选项卡切换增加平滑过渡。
    - API Key 展示区美化。

## 3. 技术栈保持
- **通信**: SSE (EventSource)
- **UI**: Ant Design 5 + CSS Variables
- **后端**: FastAPI + Asyncio Queue

## 4. 成功指标
- 网关管理页面的“实时日志”不再是模拟数据，而是真实反映系统操作。
- 全站所有页面（Gateway, Services, Tools, Chat）在视觉上具有高度统一的 Premium 感。
- 前后端通信无内存泄漏，SSE 连接在页面销毁时正确关闭。

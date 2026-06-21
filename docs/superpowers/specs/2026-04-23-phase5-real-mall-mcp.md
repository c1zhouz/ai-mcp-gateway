# Phase 5: Real E-commerce MCP Wrapper - 设计规格书

## 1. 概述

### 1.1 项目目标
基于现有业务数据库（MySQL / PostgreSQL），构建一个真实的 MCP (Model Context Protocol) 微服务（Wrapper）。该服务将通过标准的 MCP 协议将底层商城的库存查询与销售数据分析能力暴露给 AI MCP Gateway，使大模型能够直接读取真实的商业数据进行分析与预警。

### 1.2 核心价值
- 实现 AI 与真实企业业务数据库的零代码打通（通过 SQL 查询抽象为 Tool）。
- 验证 Gateway 原型与真实业务数据包装服务的集成能力。

### 1.3 技术栈
- **编程语言**: Python 3.11+
- **MCP 框架**: 官方 `mcp` 库中的 `FastMCP` (或直接集成 FastAPI SSE 方案)
- **数据库 ORM**: `SQLAlchemy` (Async 模式)
- **数据库驱动**: `aiomysql` (针对 MySQL) / `asyncpg` (针对 PostgreSQL)
- **配置管理**: `python-dotenv` 保护敏感 DB 账号密码

---

## 2. 架构设计

### 2.1 目录结构
该服务为独立微服务，与 Gateway 主代码隔离：
```
ai-mcp-gateway/
├── services/
│   ├── real_mall_mcp/
│   │   ├── .env.example
│   │   ├── requirements.txt
│   │   ├── main.py              # FastMCP / FastAPI 入口
│   │   ├── database.py          # SQLAlchemy 异步引擎和 session 管理
│   │   ├── models.py            # ORM 映射 (商品表、订单表等)
│   │   └── tools/
│   │       ├── __init__.py
│   │       ├── inventory.py     # check_inventory 工具逻辑
│   │       └── sales.py         # get_sales_report 工具逻辑
```

### 2.2 数据库实体抽象 (ORM)
针对已有数据库，Wrapper 只进行**只读(Read-Only)**查询，不修改底层数据。假设映射以下两张核心表：
1. **`products` (商品/库存表)**：包含 `id`, `name`, `category`, `price`, `stock`
2. **`orders` (订单/销售表)**：包含 `id`, `product_id`, `quantity`, `total_price`, `created_at`

---

## 3. 工具 (Tools) 定义规范

### 3.1 `check_inventory` (库存诊断工具)
- **用途**：供 AI 查询特定商品的库存，或者捞出全局库存低于某个阈值的商品列表，用于低库存预警。
- **参数 (JSON Schema)**:
  - `product_id` (string, 可选): 查询特定商品。
  - `low_stock_threshold` (integer, 可选): 如果不提供 `product_id`，则返回所有库存小于等于该阈值的商品。
- **返回结果**: 包含商品名、当前库存量、SKU等信息的 JSON 列表。

### 3.2 `get_sales_report` (销售数据分析工具)
- **用途**：供 AI 聚合查询指定时间段内的销售统计指标，便于进行财务或运营分析。
- **参数 (JSON Schema)**:
  - `start_date` (string, YYYY-MM-DD, 必填): 统计起始日期。
  - `end_date` (string, YYYY-MM-DD, 必填): 统计结束日期。
  - `category_id` (string, 可选): 如果提供，仅统计该类别的销售额。
- **返回结果**: JSON 对象，包含 `total_revenue` (总销售额), `total_orders` (总订单数), 以及按商品分组的销量排行榜。

---

## 4. 部署与集成

1. 数据库配置注入：通过 `.env` 中的 `DATABASE_URL` 动态加载，支持格式 `mysql+aiomysql://user:pass@host/db` 或 `postgresql+asyncpg://user:pass@host/db`。
2. 通过 `uvicorn main:app --port 5001` 启动 SSE Server。
3. 在 Gateway 前台输入 `http://127.0.0.1:5001/sse` 完成工具抓取与集成。

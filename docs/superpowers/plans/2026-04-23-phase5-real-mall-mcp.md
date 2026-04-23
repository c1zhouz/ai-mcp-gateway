# Phase 5: Real Mall MCP Wrapper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a real E-commerce MCP Wrapper using FastMCP and SQLAlchemy Async to expose inventory and sales data tools to AI Gateway.

**Architecture:** An independent Python microservice inside `services/real_mall_mcp`. It uses SQLAlchemy with SQLite (for mock testing) or MySQL/PostgreSQL via env vars. It exposes a standard MCP SSE endpoint via FastMCP (part of the official mcp python sdk).

**Tech Stack:** Python 3.11+, mcp (FastMCP), SQLAlchemy (async), aiosqlite, python-dotenv, uvicorn

---

### Task 1: Initialize Project Structure and Dependencies

**Files:**
- Create: `services/real_mall_mcp/requirements.txt`
- Create: `services/real_mall_mcp/.env.example`

- [ ] **Step 1: Create directories**

```bash
mkdir -p services/real_mall_mcp
```

- [ ] **Step 2: Create requirements.txt**

```text
mcp[cli]>=1.0.0
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
sqlalchemy[asyncio]>=2.0.35
aiosqlite>=0.20.0
python-dotenv>=1.0.1
pydantic>=2.9.0
```

- [ ] **Step 3: Create .env.example**

```text
DATABASE_URL=sqlite+aiosqlite:///mall_data.db
MCP_PORT=5001
```

- [ ] **Step 4: Commit**

```bash
git add services/real_mall_mcp/
git commit -m "feat: initialize real_mall_mcp service structure"
```

---

### Task 2: Database Configuration and Models

**Files:**
- Create: `services/real_mall_mcp/database.py`
- Create: `services/real_mall_mcp/models.py`
- Create: `services/real_mall_mcp/mock_data.py`

- [ ] **Step 1: Write database.py**

```python
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///mall_data.db")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def get_db_session():
    async with AsyncSessionLocal() as session:
        yield session
```

- [ ] **Step 2: Write models.py**

```python
from sqlalchemy import Column, String, Float, Integer, DateTime
from .database import Base
from datetime import datetime
import uuid

class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    category = Column(String)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)

class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    total_price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

- [ ] **Step 3: Write mock_data.py**

```python
import asyncio
from .database import engine, Base, AsyncSessionLocal
from .models import Product, Order
from datetime import datetime, timedelta

async def init_mock_data():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionLocal() as session:
        # Add Products
        p1 = Product(id="P001", name="iPhone 15 Pro", category="Electronics", price=8999.0, stock=5)
        p2 = Product(id="P002", name="MacBook Air M3", category="Electronics", price=7999.0, stock=20)
        p3 = Product(id="P003", name="Nike Air Max", category="Shoes", price=899.0, stock=2)
        session.add_all([p1, p2, p3])
        await session.commit()
        
        # Add Orders (last 7 days)
        now = datetime.utcnow()
        o1 = Order(product_id="P001", quantity=2, total_price=17998.0, created_at=now - timedelta(days=1))
        o2 = Order(product_id="P002", quantity=1, total_price=7999.0, created_at=now - timedelta(days=2))
        o3 = Order(product_id="P003", quantity=5, total_price=4495.0, created_at=now - timedelta(days=1))
        session.add_all([o1, o2, o3])
        await session.commit()

if __name__ == "__main__":
    asyncio.run(init_mock_data())
```

- [ ] **Step 4: Commit**

```bash
git add services/real_mall_mcp/
git commit -m "feat: setup database models and mock script"
```

---

### Task 3: FastMCP Application and Tools

**Files:**
- Create: `services/real_mall_mcp/main.py`

- [ ] **Step 1: Write main.py with FastMCP Tools**

```python
import os
from datetime import datetime
from typing import Optional
from mcp.server.fastmcp import FastMCP
from sqlalchemy import select, func
from dotenv import load_dotenv
from .database import AsyncSessionLocal
from .models import Product, Order

load_dotenv()

# Create FastMCP Server
mcp = FastMCP("Real Mall MCP Server")

@mcp.tool()
async def check_inventory(product_id: Optional[str] = None, low_stock_threshold: Optional[int] = None) -> list[dict]:
    """
    检查商品库存状态。
    如果指定 product_id，则精确查询。
    如果指定 low_stock_threshold，则返回所有库存小于等于该阈值的商品，用于低库存预警。
    """
    async with AsyncSessionLocal() as session:
        stmt = select(Product)
        if product_id:
            stmt = stmt.where(Product.id == product_id)
        if low_stock_threshold is not None:
            stmt = stmt.where(Product.stock <= low_stock_threshold)
            
        result = await session.execute(stmt)
        products = result.scalars().all()
        
        return [
            {
                "product_id": p.id,
                "name": p.name,
                "category": p.category,
                "price": p.price,
                "stock": p.stock
            } for p in products
        ]

@mcp.tool()
async def get_sales_report(start_date: str, end_date: str, category: Optional[str] = None) -> dict:
    """
    获取指定日期区间（YYYY-MM-DD）的销售报表。包含总收入、订单总数以及分商品统计。
    """
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return {"error": "Invalid date format, use YYYY-MM-DD"}
        
    async with AsyncSessionLocal() as session:
        # Base query
        stmt = select(Order, Product).join(Product, Order.product_id == Product.id)\
            .where(Order.created_at >= start_dt)\
            .where(Order.created_at <= end_dt)
            
        if category:
            stmt = stmt.where(Product.category == category)
            
        result = await session.execute(stmt)
        records = result.all()
        
        total_revenue = sum(r.Order.total_price for r in records)
        total_orders = len(records)
        
        # Product breakdown
        breakdown = {}
        for r in records:
            p_name = r.Product.name
            if p_name not in breakdown:
                breakdown[p_name] = {"quantity": 0, "revenue": 0}
            breakdown[p_name]["quantity"] += r.Order.quantity
            breakdown[p_name]["revenue"] += r.Order.total_price
            
        return {
            "period": f"{start_date} to {end_date}",
            "total_revenue": total_revenue,
            "total_orders": total_orders,
            "product_breakdown": breakdown
        }

if __name__ == "__main__":
    port = int(os.getenv("MCP_PORT", "5001"))
    # Run the FastMCP server with SSE transport
    mcp.run("sse", port=port)
```

- [ ] **Step 2: Commit**

```bash
git add services/real_mall_mcp/
git commit -m "feat: implement FastMCP tools for inventory and sales"
```

---

### Task 4: Setup execution and verification

- [ ] **Step 1: Install dependencies and generate DB**

```bash
cd services/real_mall_mcp
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m services.real_mall_mcp.mock_data
```

- [ ] **Step 2: Final sanity check**

*(Developer will run the server locally to ensure it starts)*

```bash
cd services/real_mall_mcp
source venv/bin/activate
python -m services.real_mall_mcp.main
```
*(Server should run on http://0.0.0.0:5001 without crashing)*

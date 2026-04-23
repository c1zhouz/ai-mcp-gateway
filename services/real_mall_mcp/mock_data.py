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

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
    mcp.settings.port = port
    # Run the FastMCP server with SSE transport
    mcp.run("sse")

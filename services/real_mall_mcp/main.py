import os
from datetime import datetime
from typing import Optional
from mcp.server.fastmcp import FastMCP
from sqlalchemy import select, func
from dotenv import load_dotenv
from database import AsyncSessionLocal
from models import Sku, GroupBuyOrderList

load_dotenv()

# Create FastMCP Server
mcp = FastMCP("Real Mall MCP Server")

@mcp.tool()
async def list_goods(goods_id: Optional[str] = None) -> list[dict]:
    """
    查询商城的商品(SKU)信息及价格。
    如果指定 goods_id，则精确查询。
    否则返回所有商品的列表。
    """
    async with AsyncSessionLocal() as session:
        stmt = select(Sku)
        if goods_id:
            stmt = stmt.where(Sku.goods_id == goods_id)
            
        result = await session.execute(stmt)
        skus = result.scalars().all()
        
        return [
            {
                "goods_id": s.goods_id,
                "goods_name": s.goods_name,
                "original_price": float(s.original_price) if s.original_price else 0.0,
                "source": s.source,
                "channel": s.channel
            } for s in skus
        ]

@mcp.tool()
async def get_sales_report(start_date: str, end_date: str) -> dict:
    """
    获取指定日期区间（YYYY-MM-DD）的拼团销售报表。包含总成单金额、订单总数以及分商品的成单统计。
    """
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return {"error": "Invalid date format, use YYYY-MM-DD"}
        
    async with AsyncSessionLocal() as session:
        # Base query joining group_buy_order_list with sku on goods_id
        stmt = select(GroupBuyOrderList, Sku).outerjoin(Sku, GroupBuyOrderList.goods_id == Sku.goods_id)\
            .where(GroupBuyOrderList.create_time >= start_dt)\
            .where(GroupBuyOrderList.create_time <= end_dt)
            
        result = await session.execute(stmt)
        records = result.all()
        
        # Calculate revenue based on original_price - deduction_price
        total_revenue = 0.0
        total_orders = len(records)
        breakdown = {}
        
        for r in records:
            order = r.GroupBuyOrderList
            sku = r.Sku
            
            # calculate pay price approximately
            pay_price = float(order.original_price or 0) - float(order.deduction_price or 0)
            total_revenue += pay_price
            
            goods_name = sku.goods_name if sku else f"Unknown({order.goods_id})"
            
            if goods_name not in breakdown:
                breakdown[goods_name] = {"quantity": 0, "revenue": 0.0}
            breakdown[goods_name]["quantity"] += 1
            breakdown[goods_name]["revenue"] += pay_price
            
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

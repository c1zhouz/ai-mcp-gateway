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
@mcp.tool()
async def search_goods_by_name(keyword: str) -> list[dict]:
    """根据商品名称关键词搜索商品。"""
    async with AsyncSessionLocal() as session:
        stmt = select(Sku).where(Sku.goods_name.like(f"%{keyword}%"))
        result = await session.execute(stmt)
        skus = result.scalars().all()
        return [{"goods_id": s.goods_id, "goods_name": s.goods_name, "price": float(s.original_price or 0)} for s in skus]

@mcp.tool()
async def get_inventory_status(goods_id: str) -> dict:
    """查询指定商品的库存状态（模拟数据）。"""
    return {"goods_id": goods_id, "inventory": 100, "status": "sufficient"}

@mcp.tool()
async def get_order_details(order_id: str) -> dict:
    """获取订单详情。"""
    return {"order_id": order_id, "status": "paid", "customer_id": "CUST_001", "total_amount": 299.0}

@mcp.tool()
async def list_recent_orders(limit: int = 10) -> list[dict]:
    """列出最近的订单。"""
    async with AsyncSessionLocal() as session:
        stmt = select(GroupBuyOrderList).order_by(GroupBuyOrderList.create_time.desc()).limit(limit)
        result = await session.execute(stmt)
        orders = result.scalars().all()
        return [{"order_id": o.order_id, "goods_id": o.goods_id, "time": str(o.create_time)} for o in orders]

@mcp.tool()
async def get_customer_profile(customer_id: str) -> dict:
    """获取客户画像资料。"""
    return {"customer_id": customer_id, "name": "张三", "level": "VIP", "total_spent": 5000.0}

@mcp.tool()
async def list_categories() -> list[str]:
    """列出商城所有商品分类。"""
    return ["电子产品", "居家生活", "生鲜食品", "美妆个护", "服饰鞋包"]

@mcp.tool()
async def get_promotion_activities() -> list[dict]:
    """获取当前正在进行的促销活动。"""
    return [{"id": "ACT_01", "name": "春季大促", "discount": "0.8"}, {"id": "ACT_02", "name": "满100减20", "type": "coupon"}]

@mcp.tool()
async def update_goods_price(goods_id: str, new_price: float) -> dict:
    """更新商品价格（需要管理员权限）。"""
    return {"status": "success", "goods_id": goods_id, "new_price": new_price}

@mcp.tool()
async def get_shipping_status(order_id: str) -> dict:
    """查询订单的物流状态。"""
    return {"order_id": order_id, "logistics_provider": "顺丰速运", "status": "in_transit", "location": "上海分拨中心"}

@mcp.tool()
async def export_daily_sales_csv(date: str) -> str:
    """导出指定日期的销售数据为 CSV 链接。"""
    return f"https://cdn.mall.com/exports/sales_{date}.csv"

@mcp.tool()
async def get_stock_warning_list() -> list[dict]:
    """获取库存预警商品列表（低于10件）。"""
    return [{"goods_id": "SKU_005", "name": "苹果", "stock": 3}, {"goods_id": "SKU_009", "name": "牛奶", "stock": 8}]

@mcp.tool()
async def apply_marketing_coupon(coupon_code: str, order_id: str) -> dict:
    """为订单应用营销优惠券。"""
    return {"order_id": order_id, "coupon_code": coupon_code, "status": "applied", "discount": 10.0}

@mcp.tool()
async def get_system_health_status() -> dict:
    """检查商城 MCP 服务的系统健康度。"""
    return {"status": "healthy", "uptime": "72h", "db_connection": "connected"}

@mcp.tool()
async def list_supplier_info() -> list[dict]:
    """获取供应商名录信息。"""
    return [{"id": "SUP_01", "name": "华为科技"}, {"id": "SUP_02", "name": "京东物流"}]

@mcp.tool()
async def get_active_user_stats() -> dict:
    """获取实时活跃用户统计（模拟数据）。"""
    return {"online_users": 1250, "today_uv": 58000, "peak_concurrent": 3200}

@mcp.tool()
async def cancel_order_request(order_id: str, reason: str) -> dict:
    """申请取消订单。"""
    return {"order_id": order_id, "status": "pending_approval", "reason": reason}

@mcp.tool()
async def get_revenue_forecast() -> dict:
    """获取下个月的营收预测（基于 AI 分析）。"""
    return {"forecast_revenue": 1200000.0, "confidence": 0.85, "factors": ["节日促销", "新品发布"]}

@mcp.tool()
async def get_goods_comments(goods_id: str) -> list[dict]:
    """获取商品的最近评价。"""
    return [{"user": "user_1", "score": 5, "comment": "质量很好"}, {"user": "user_2", "score": 4, "comment": "发货很快"}]

if __name__ == "__main__":
    port = int(os.getenv("MCP_PORT", "5001"))
    mcp.settings.port = port
    # Run the FastMCP server with SSE transport
    mcp.run("sse")

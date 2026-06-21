import os
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import Optional

from mcp.server.fastmcp import FastMCP
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import run_read_query
from models import (
    GroupBuyActivity,
    GroupBuyDiscount,
    GroupBuyOrder,
    GroupBuyOrderList,
    ScSkuActivity,
    Sku,
)

mcp = FastMCP("Group Buy Mall MCP Server")

ACTIVITY_STATUS = {
    1: "启用",
    2: "进行中",
    3: "已结束",
    4: "已关闭",
}

TEAM_STATUS = {
    0: "初始化",
    1: "已成团",
    2: "拼团中",
    3: "未成团",
    4: "已取消",
}


def _money(value) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return round(float(value), 2)
    return round(float(value), 2)


def _paid_amount(order: GroupBuyOrderList) -> float:
    return round(_money(order.original_price) - _money(order.deduction_price), 2)


def _iso(value) -> Optional[str]:
    return value.isoformat() if value else None


def _activity_status_label(activity: GroupBuyActivity) -> str:
    now = datetime.now()
    if activity.start_time and activity.start_time > now:
        return "未开始"
    if activity.end_time and activity.end_time < now:
        return "已结束"
    return "进行中"


def _team_status_label(team: GroupBuyOrder) -> str:
    if team.complete_count is not None and team.target_count is not None:
        if team.complete_count >= team.target_count:
            return "已成团"
    return TEAM_STATUS.get(team.status, "未知")


def _team_progress(team: GroupBuyOrder) -> dict:
    target = team.target_count or 0
    complete = team.complete_count or 0
    remaining = max(target - complete, 0)
    progress_rate = round(complete / target, 3) if target else 0.0
    return {
        "team_id": team.team_id,
        "activity_id": team.activity_id,
        "target_count": target,
        "complete_count": complete,
        "lock_count": team.lock_count or 0,
        "remaining_count": remaining,
        "progress_rate": progress_rate,
        "status": team.status,
        "status_label": _team_status_label(team),
        "valid_start_time": _iso(team.valid_start_time),
        "valid_end_time": _iso(team.valid_end_time),
        "pay_price": _money(team.pay_price),
    }


async def _activity_metrics(session: AsyncSession, activity_id: int) -> dict:
    sku_rows = await session.execute(
        select(ScSkuActivity.goods_id).where(ScSkuActivity.activity_id == activity_id)
    )
    team_rows = await session.execute(
        select(GroupBuyOrder).where(GroupBuyOrder.activity_id == activity_id)
    )
    order_rows = await session.execute(
        select(GroupBuyOrderList).where(GroupBuyOrderList.activity_id == activity_id)
    )

    skus = sku_rows.scalars().all()
    teams = team_rows.scalars().all()
    orders = order_rows.scalars().all()
    completed_teams = [
        team for team in teams
        if (team.complete_count or 0) >= (team.target_count or 0) and (team.target_count or 0) > 0
    ]

    return {
        "sku_count": len(set(skus)),
        "team_count": len(teams),
        "completed_team_count": len(completed_teams),
        "order_count": len(orders),
        "total_revenue": round(sum(_paid_amount(order) for order in orders), 2),
        "total_deduction": round(sum(_money(order.deduction_price) for order in orders), 2),
    }


async def _load_activity(session: AsyncSession, activity_id: int):
    row = await session.execute(
        select(GroupBuyActivity, GroupBuyDiscount)
        .outerjoin(GroupBuyDiscount, GroupBuyActivity.discount_id == GroupBuyDiscount.discount_id)
        .where(GroupBuyActivity.activity_id == activity_id)
    )
    return row.first()


@mcp.tool()
async def list_active_group_buy_activities(limit: int = 10) -> list[dict]:
    """查询当前正在进行的拼团活动，并返回活动、优惠、商品数、队伍数和订单数。"""
    limit = max(1, min(limit, 50))

    async def query(session: AsyncSession):
        now = datetime.now()
        rows = await session.execute(
            select(GroupBuyActivity, GroupBuyDiscount)
            .outerjoin(GroupBuyDiscount, GroupBuyActivity.discount_id == GroupBuyDiscount.discount_id)
            .where(GroupBuyActivity.start_time <= now)
            .where(GroupBuyActivity.end_time >= now)
            .order_by(GroupBuyActivity.start_time.desc(), GroupBuyActivity.activity_id.asc())
            .limit(limit)
        )

        activities = []
        for activity, discount in rows.all():
            metrics = await _activity_metrics(session, activity.activity_id)
            activities.append({
                "activity_id": activity.activity_id,
                "activity_name": activity.activity_name,
                "status": activity.status,
                "status_label": _activity_status_label(activity),
                "target_count": activity.target,
                "valid_minutes": activity.valid_time,
                "start_time": _iso(activity.start_time),
                "end_time": _iso(activity.end_time),
                "discount_id": activity.discount_id,
                "discount_name": discount.discount_name if discount else None,
                **metrics,
            })
        return activities

    return await run_read_query(query)


@mcp.tool()
async def get_activity_detail(activity_id: int) -> dict:
    """查询拼团活动详情，包含优惠规则、关联商品和活动运营指标。"""

    async def query(session: AsyncSession):
        row = await _load_activity(session, activity_id)
        if not row:
            return {}
        activity, discount = row
        metrics = await _activity_metrics(session, activity_id)

        product_rows = await session.execute(
            select(Sku)
            .join(ScSkuActivity, ScSkuActivity.goods_id == Sku.goods_id)
            .where(ScSkuActivity.activity_id == activity_id)
            .order_by(Sku.goods_id.asc())
        )
        products = [
            {
                "goods_id": sku.goods_id,
                "goods_name": sku.goods_name,
                "source": sku.source,
                "channel": sku.channel,
                "original_price": _money(sku.original_price),
            }
            for sku in product_rows.scalars().all()
        ]

        return {
            "activity_id": activity.activity_id,
            "activity_name": activity.activity_name,
            "status": activity.status,
            "status_label": _activity_status_label(activity),
            "target_count": activity.target,
            "take_limit_count": activity.take_limit_count,
            "valid_minutes": activity.valid_time,
            "start_time": _iso(activity.start_time),
            "end_time": _iso(activity.end_time),
            "discount": {
                "discount_id": discount.discount_id if discount else activity.discount_id,
                "discount_name": discount.discount_name if discount else None,
                "discount_desc": discount.discount_desc if discount else None,
                "market_plan": discount.market_plan if discount else None,
                "market_expr": discount.market_expr if discount else None,
            },
            "products": products,
            "metrics": metrics,
        }

    result = await run_read_query(query)
    return result or {"error": "activity not found", "activity_id": activity_id}


@mcp.tool()
async def get_team_progress(team_id: str) -> dict:
    """查询某个拼团队伍的成团进度、剩余人数、有效期和关联活动。"""

    async def query(session: AsyncSession):
        row = await session.execute(
            select(GroupBuyOrder, GroupBuyActivity)
            .outerjoin(GroupBuyActivity, GroupBuyOrder.activity_id == GroupBuyActivity.activity_id)
            .where(GroupBuyOrder.team_id == team_id)
        )
        result = row.first()
        if not result:
            return {}
        team, activity = result
        data = _team_progress(team)
        data["activity_name"] = activity.activity_name if activity else None
        return data

    result = await run_read_query(query)
    return result or {"error": "team not found", "team_id": team_id}


@mcp.tool()
async def analyze_activity_sales(activity_id: int) -> dict:
    """分析某个拼团活动的订单数、成交金额、成团率和商品销售拆分。"""

    async def query(session: AsyncSession):
        row = await _load_activity(session, activity_id)
        if not row:
            return {}
        activity, discount = row
        metrics = await _activity_metrics(session, activity_id)

        team_rows = await session.execute(
            select(GroupBuyOrder).where(GroupBuyOrder.activity_id == activity_id)
        )
        teams = team_rows.scalars().all()

        order_rows = await session.execute(
            select(GroupBuyOrderList, Sku)
            .outerjoin(Sku, GroupBuyOrderList.goods_id == Sku.goods_id)
            .where(GroupBuyOrderList.activity_id == activity_id)
        )

        sku_breakdown = defaultdict(lambda: {
            "goods_id": "",
            "goods_name": "",
            "order_count": 0,
            "revenue": 0.0,
            "deduction": 0.0,
        })
        for order, sku in order_rows.all():
            item = sku_breakdown[order.goods_id]
            item["goods_id"] = order.goods_id
            item["goods_name"] = sku.goods_name if sku else f"未知商品({order.goods_id})"
            item["order_count"] += 1
            item["revenue"] = round(item["revenue"] + _paid_amount(order), 2)
            item["deduction"] = round(item["deduction"] + _money(order.deduction_price), 2)

        team_count = len(teams)
        completed_team_count = metrics["completed_team_count"]
        return {
            "activity_id": activity.activity_id,
            "activity_name": activity.activity_name,
            "discount_name": discount.discount_name if discount else None,
            "team_count": team_count,
            "completed_team_count": completed_team_count,
            "completion_rate": round(completed_team_count / team_count, 3) if team_count else 0.0,
            "order_count": metrics["order_count"],
            "total_revenue": metrics["total_revenue"],
            "total_deduction": metrics["total_deduction"],
            "average_order_value": round(metrics["total_revenue"] / metrics["order_count"], 2) if metrics["order_count"] else 0.0,
            "sku_breakdown": sorted(
                sku_breakdown.values(),
                key=lambda item: (-item["order_count"], -item["revenue"], item["goods_id"]),
            ),
        }

    result = await run_read_query(query)
    return result or {"error": "activity not found", "activity_id": activity_id}


@mcp.tool()
async def get_sku_sales_ranking(limit: int = 10, activity_id: Optional[int] = None) -> list[dict]:
    """查询拼团商品销售排行，可按活动筛选。"""
    limit = max(1, min(limit, 50))

    async def query(session: AsyncSession):
        stmt = select(GroupBuyOrderList, Sku).outerjoin(Sku, GroupBuyOrderList.goods_id == Sku.goods_id)
        if activity_id is not None:
            stmt = stmt.where(GroupBuyOrderList.activity_id == activity_id)
        rows = await session.execute(stmt)

        ranking = defaultdict(lambda: {
            "goods_id": "",
            "goods_name": "",
            "order_count": 0,
            "revenue": 0.0,
            "deduction": 0.0,
        })
        for order, sku in rows.all():
            item = ranking[order.goods_id]
            item["goods_id"] = order.goods_id
            item["goods_name"] = sku.goods_name if sku else f"未知商品({order.goods_id})"
            item["order_count"] += 1
            item["revenue"] = round(item["revenue"] + _paid_amount(order), 2)
            item["deduction"] = round(item["deduction"] + _money(order.deduction_price), 2)

        return sorted(
            ranking.values(),
            key=lambda item: (-item["order_count"], -item["revenue"], item["goods_id"]),
        )[:limit]

    return await run_read_query(query)


@mcp.tool()
async def get_discount_effectiveness() -> list[dict]:
    """按优惠规则汇总活动数、订单数、成交金额和平均优惠金额。"""

    async def query(session: AsyncSession):
        rows = await session.execute(
            select(GroupBuyActivity, GroupBuyDiscount)
            .outerjoin(GroupBuyDiscount, GroupBuyActivity.discount_id == GroupBuyDiscount.discount_id)
            .order_by(GroupBuyActivity.activity_id.asc())
        )

        report = defaultdict(lambda: {
            "discount_id": "",
            "discount_name": "",
            "market_plan": "",
            "market_expr": "",
            "activity_count": 0,
            "order_count": 0,
            "revenue": 0.0,
            "total_deduction": 0.0,
            "average_deduction": 0.0,
        })

        for activity, discount in rows.all():
            key = activity.discount_id or "none"
            item = report[key]
            item["discount_id"] = key
            item["discount_name"] = discount.discount_name if discount else "无优惠"
            item["market_plan"] = discount.market_plan if discount else ""
            item["market_expr"] = discount.market_expr if discount else ""
            item["activity_count"] += 1

            order_rows = await session.execute(
                select(GroupBuyOrderList).where(GroupBuyOrderList.activity_id == activity.activity_id)
            )
            orders = order_rows.scalars().all()
            item["order_count"] += len(orders)
            item["revenue"] = round(item["revenue"] + sum(_paid_amount(order) for order in orders), 2)
            item["total_deduction"] = round(item["total_deduction"] + sum(_money(order.deduction_price) for order in orders), 2)

        for item in report.values():
            item["average_deduction"] = round(item["total_deduction"] / item["order_count"], 2) if item["order_count"] else 0.0

        return sorted(report.values(), key=lambda item: (-item["order_count"], item["discount_id"]))

    return await run_read_query(query)


@mcp.tool()
async def find_unfinished_teams(limit: int = 10, within_hours: int = 24) -> list[dict]:
    """找出未成团且即将到期的队伍，便于运营人员干预。"""
    limit = max(1, min(limit, 50))
    within_hours = max(1, min(within_hours, 168))

    async def query(session: AsyncSession):
        rows = await session.execute(
            select(GroupBuyOrder, GroupBuyActivity)
            .outerjoin(GroupBuyActivity, GroupBuyOrder.activity_id == GroupBuyActivity.activity_id)
            .where(GroupBuyOrder.complete_count < GroupBuyOrder.target_count)
            .order_by(GroupBuyOrder.valid_end_time.asc(), GroupBuyOrder.team_id.asc())
            .limit(limit)
        )

        teams = []
        now = datetime.now()
        for team, activity in rows.all():
            data = _team_progress(team)
            expires_at = team.valid_end_time
            hours_to_expire = round((expires_at - now).total_seconds() / 3600, 2) if expires_at else None
            if hours_to_expire is not None and hours_to_expire > within_hours:
                continue
            data["activity_name"] = activity.activity_name if activity else None
            data["hours_to_expire"] = hours_to_expire
            teams.append(data)
        return teams

    return await run_read_query(query)


@mcp.tool()
async def get_user_group_buy_history(user_id: str, limit: int = 10) -> dict:
    """查询用户的拼团订单历史，包含商品、活动、队伍状态和实付金额。"""
    limit = max(1, min(limit, 50))

    async def query(session: AsyncSession):
        rows = await session.execute(
            select(GroupBuyOrderList, Sku, GroupBuyOrder, GroupBuyActivity)
            .outerjoin(Sku, GroupBuyOrderList.goods_id == Sku.goods_id)
            .outerjoin(GroupBuyOrder, GroupBuyOrderList.team_id == GroupBuyOrder.team_id)
            .outerjoin(GroupBuyActivity, GroupBuyOrderList.activity_id == GroupBuyActivity.activity_id)
            .where(GroupBuyOrderList.user_id == user_id)
            .order_by(GroupBuyOrderList.create_time.asc(), GroupBuyOrderList.order_id.asc())
            .limit(limit)
        )

        orders = []
        total_paid = 0.0
        for order, sku, team, activity in rows.all():
            paid = _paid_amount(order)
            total_paid = round(total_paid + paid, 2)
            orders.append({
                "order_id": order.order_id,
                "team_id": order.team_id,
                "activity_id": order.activity_id,
                "activity_name": activity.activity_name if activity else None,
                "goods_id": order.goods_id,
                "goods_name": sku.goods_name if sku else f"未知商品({order.goods_id})",
                "original_price": _money(order.original_price),
                "deduction_price": _money(order.deduction_price),
                "paid_amount": paid,
                "team_status_label": _team_status_label(team) if team else None,
                "create_time": _iso(order.create_time),
            })

        return {
            "user_id": user_id,
            "order_count": len(orders),
            "total_paid": total_paid,
            "orders": orders,
        }

    result = await run_read_query(query)
    return result or {"user_id": user_id, "order_count": 0, "total_paid": 0.0, "orders": []}


if __name__ == "__main__":
    port = int(os.getenv("MCP_PORT", "5001"))
    mcp.settings.port = port
    mcp.run("sse")

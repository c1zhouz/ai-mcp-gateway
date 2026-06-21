import os
import tempfile
import unittest
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

TEST_DB = Path(tempfile.gettempdir()) / "real_mall_mcp_demo_test.db"
TEST_URL = f"sqlite+aiosqlite:///{TEST_DB}"

os.environ["DATABASE_URL"] = TEST_URL

from database import Base, engine
from main import (
    analyze_activity_sales,
    find_unfinished_teams,
    get_activity_detail,
    get_discount_effectiveness,
    get_sku_sales_ranking,
    get_team_progress,
    get_user_group_buy_history,
    list_active_group_buy_activities,
)
from models import (
    CrowdTags,
    GroupBuyActivity,
    GroupBuyDiscount,
    GroupBuyOrder,
    GroupBuyOrderList,
    ScSkuActivity,
    Sku,
)


class RealMallDemoToolsTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await engine.dispose()
        if TEST_DB.exists():
            TEST_DB.unlink()
        await seed_test_data()

    async def asyncTearDown(self):
        await engine.dispose()

    async def test_lists_active_group_buy_activities_with_business_metrics(self):
        activities = await list_active_group_buy_activities()

        self.assertGreaterEqual(len(activities), 2)
        self.assertIn(200456, {activity["activity_id"] for activity in activities})
        first = activities[0]
        self.assertIn("activity_id", first)
        self.assertIn("activity_name", first)
        self.assertIn("discount_name", first)
        self.assertIn("sku_count", first)
        self.assertIn("team_count", first)
        self.assertIn("order_count", first)

    async def test_activity_detail_includes_discount_and_products(self):
        detail = await get_activity_detail(100123)

        self.assertEqual(detail["activity_id"], 100123)
        self.assertEqual(detail["target_count"], 3)
        self.assertEqual(detail["discount"]["discount_name"], "满减优惠100-10元")
        self.assertGreaterEqual(len(detail["products"]), 2)
        self.assertEqual(detail["products"][0]["goods_id"], "1101001")

    async def test_team_progress_returns_completion_state(self):
        progress = await get_team_progress("TEAM1002")

        self.assertEqual(progress["team_id"], "TEAM1002")
        self.assertEqual(progress["target_count"], 3)
        self.assertEqual(progress["complete_count"], 2)
        self.assertEqual(progress["remaining_count"], 1)
        self.assertEqual(progress["progress_rate"], 0.667)
        self.assertEqual(progress["status_label"], "拼团中")

    async def test_activity_sales_analysis_summarizes_orders_and_revenue(self):
        analysis = await analyze_activity_sales(100123)

        self.assertEqual(analysis["activity_id"], 100123)
        self.assertEqual(analysis["team_count"], 3)
        self.assertEqual(analysis["completed_team_count"], 1)
        self.assertEqual(analysis["order_count"], 6)
        self.assertGreater(analysis["total_revenue"], 0)
        self.assertGreaterEqual(len(analysis["sku_breakdown"]), 2)

    async def test_sku_sales_ranking_uses_order_data(self):
        ranking = await get_sku_sales_ranking(limit=3)

        self.assertEqual(ranking[0]["goods_id"], "1101001")
        self.assertEqual(ranking[0]["goods_name"], "iPhone 17")
        self.assertEqual(ranking[0]["order_count"], 4)
        self.assertGreater(ranking[0]["revenue"], ranking[1]["revenue"])

    async def test_discount_effectiveness_groups_by_discount_rule(self):
        report = await get_discount_effectiveness()

        names = {item["discount_name"] for item in report}
        self.assertIn("满减优惠100-10元", names)
        self.assertIn("折扣优惠8折", names)
        self.assertTrue(all("average_deduction" in item for item in report))

    async def test_finds_unfinished_teams_for_operations_attention(self):
        teams = await find_unfinished_teams(limit=5)

        team_ids = {team["team_id"] for team in teams}
        self.assertIn("TEAM1002", team_ids)
        self.assertIn("TEAM1003", team_ids)
        self.assertTrue(all(team["remaining_count"] > 0 for team in teams))

    async def test_user_group_buy_history_shows_orders_and_team_status(self):
        history = await get_user_group_buy_history("u1001")

        self.assertEqual(history["user_id"], "u1001")
        self.assertEqual(history["order_count"], 3)
        self.assertGreater(history["total_paid"], 0)
        self.assertEqual(history["orders"][0]["goods_name"], "iPhone 17")


async def seed_test_data():
    now = datetime.now().replace(microsecond=0)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    from database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        session.add_all([
            Sku(id=1, source="s01", channel="c01", goods_id="1101001", goods_name="iPhone 17", original_price=Decimal("5999.00"), create_time=now, update_time=now),
            Sku(id=2, source="s01", channel="c01", goods_id="1101002", goods_name="iPhone 17 Pro", original_price=Decimal("8999.00"), create_time=now, update_time=now),
            Sku(id=3, source="s01", channel="c02", goods_id="1102001", goods_name="米家扫地机器人", original_price=Decimal("1999.00"), create_time=now, update_time=now),
            Sku(id=4, source="s01", channel="c02", goods_id="1103001", goods_name="智能咖啡机", original_price=Decimal("1299.00"), create_time=now, update_time=now),
            GroupBuyDiscount(id=1, discount_id="25120208", discount_name="满减优惠100-10元", discount_desc="订单满100元减10元", discount_type=0, market_plan="MJ", market_expr="100,10", create_time=now, update_time=now),
            GroupBuyDiscount(id=2, discount_id="25120209", discount_name="折扣优惠8折", discount_desc="拼团订单享8折", discount_type=0, market_plan="ZK", market_expr="0.8", create_time=now, update_time=now),
            GroupBuyActivity(id=1, activity_id=100123, activity_name="3人拼团数码专场", discount_id="25120208", group_type=0, take_limit_count=1, target=3, valid_time=60, status=2, start_time=now - timedelta(days=5), end_time=now + timedelta(days=10), create_time=now - timedelta(days=5), update_time=now),
            GroupBuyActivity(id=2, activity_id=200456, activity_name="5人拼团家电专场", discount_id="25120209", group_type=0, take_limit_count=1, target=5, valid_time=90, status=1, start_time=now - timedelta(days=3), end_time=now + timedelta(days=8), create_time=now - timedelta(days=3), update_time=now),
            ScSkuActivity(id=1, source="s01", channel="c01", activity_id=100123, goods_id="1101001", create_time=now, update_time=now),
            ScSkuActivity(id=2, source="s01", channel="c01", activity_id=100123, goods_id="1101002", create_time=now, update_time=now),
            ScSkuActivity(id=3, source="s01", channel="c02", activity_id=200456, goods_id="1102001", create_time=now, update_time=now),
            ScSkuActivity(id=4, source="s01", channel="c02", activity_id=200456, goods_id="1103001", create_time=now, update_time=now),
            _team(1, "TEAM1001", 100123, 3, 3, 1, Decimal("5989.00"), now - timedelta(days=2), now + timedelta(hours=8)),
            _team(2, "TEAM1002", 100123, 3, 2, 2, Decimal("5989.00"), now - timedelta(hours=4), now + timedelta(hours=2)),
            _team(3, "TEAM1003", 100123, 3, 1, 2, Decimal("8989.00"), now - timedelta(hours=1), now + timedelta(hours=1)),
            _team(4, "TEAM2001", 200456, 5, 5, 1, Decimal("1599.20"), now - timedelta(days=1), now + timedelta(hours=10)),
            _order(1, "u1001", "TEAM1001", "P1001", 100123, "1101001", Decimal("5999.00"), Decimal("10.00"), now - timedelta(days=2)),
            _order(2, "u1002", "TEAM1001", "P1002", 100123, "1101001", Decimal("5999.00"), Decimal("10.00"), now - timedelta(days=2)),
            _order(3, "u1003", "TEAM1001", "P1003", 100123, "1101002", Decimal("8999.00"), Decimal("10.00"), now - timedelta(days=2)),
            _order(4, "u1001", "TEAM1002", "P1004", 100123, "1101001", Decimal("5999.00"), Decimal("10.00"), now - timedelta(hours=4)),
            _order(5, "u1004", "TEAM1002", "P1005", 100123, "1101001", Decimal("5999.00"), Decimal("10.00"), now - timedelta(hours=3)),
            _order(6, "u1001", "TEAM1003", "P1006", 100123, "1101002", Decimal("8999.00"), Decimal("10.00"), now - timedelta(hours=1)),
            _order(7, "u2001", "TEAM2001", "P2001", 200456, "1102001", Decimal("1999.00"), Decimal("399.80"), now - timedelta(days=1)),
            _order(8, "u2002", "TEAM2001", "P2002", 200456, "1103001", Decimal("1299.00"), Decimal("259.80"), now - timedelta(days=1)),
            CrowdTags(id=1, tag_id="TAG001", tag_name="高价值用户", tag_desc="近30天有多次拼团购买行为的用户", statistics='{"users": 128}', create_time=now, update_time=now),
        ])
        await session.commit()


def _team(id_, team_id, activity_id, target, complete, status, pay_price, start, end):
    return GroupBuyOrder(
        id=id_,
        team_id=team_id,
        activity_id=activity_id,
        source="s01",
        channel="c01",
        original_price=pay_price,
        deduction_price=Decimal("10.00"),
        pay_price=pay_price,
        target_count=target,
        complete_count=complete,
        lock_count=complete,
        status=status,
        valid_start_time=start,
        valid_end_time=end,
        notify_url="http://127.0.0.1:8091/api/v1/test/group_buy_notify",
        create_time=start,
        update_time=start,
    )


def _order(id_, user_id, team_id, order_id, activity_id, goods_id, original_price, deduction_price, created_at):
    return GroupBuyOrderList(
        id=id_,
        user_id=user_id,
        team_id=team_id,
        order_id=order_id,
        activity_id=activity_id,
        start_time=created_at,
        end_time=created_at + timedelta(hours=1),
        goods_id=goods_id,
        source="s01",
        channel="c01",
        original_price=original_price,
        deduction_price=deduction_price,
        status=1,
        out_trade_no=order_id,
        out_trade_time=created_at,
        biz_id=f"{team_id}-{order_id}",
        create_time=created_at,
        update_time=created_at,
    )

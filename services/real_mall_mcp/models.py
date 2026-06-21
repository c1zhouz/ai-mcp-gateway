from sqlalchemy import Column, DateTime, DECIMAL, Integer, String

from database import Base


class Sku(Base):
    __tablename__ = "sku"

    id = Column(Integer, primary_key=True)
    source = Column(String(8))
    channel = Column(String(8))
    goods_id = Column(String(16), index=True)
    goods_name = Column(String(128))
    original_price = Column(DECIMAL(10, 2))
    create_time = Column(DateTime)
    update_time = Column(DateTime)


class GroupBuyActivity(Base):
    __tablename__ = "group_buy_activity"

    id = Column(Integer, primary_key=True)
    activity_id = Column(Integer, index=True)
    activity_name = Column(String(128))
    discount_id = Column(String(16), index=True)
    group_type = Column(Integer)
    take_limit_count = Column(Integer)
    target = Column(Integer)
    valid_time = Column(Integer)
    status = Column(Integer)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    tag_id = Column(String(16))
    tag_scope = Column(String(32))
    create_time = Column(DateTime)
    update_time = Column(DateTime)


class GroupBuyDiscount(Base):
    __tablename__ = "group_buy_discount"

    id = Column(Integer, primary_key=True)
    discount_id = Column(String(16), index=True)
    discount_name = Column(String(128))
    discount_desc = Column(String(255))
    discount_type = Column(Integer)
    market_plan = Column(String(16))
    market_expr = Column(String(64))
    tag_id = Column(String(16))
    create_time = Column(DateTime)
    update_time = Column(DateTime)


class GroupBuyOrder(Base):
    __tablename__ = "group_buy_order"

    id = Column(Integer, primary_key=True)
    team_id = Column(String(16), index=True)
    activity_id = Column(Integer, index=True)
    source = Column(String(8))
    channel = Column(String(8))
    original_price = Column(DECIMAL(10, 2))
    deduction_price = Column(DECIMAL(10, 2))
    pay_price = Column(DECIMAL(10, 2))
    target_count = Column(Integer)
    complete_count = Column(Integer)
    lock_count = Column(Integer)
    status = Column(Integer)
    valid_start_time = Column(DateTime)
    valid_end_time = Column(DateTime)
    notify_url = Column(String(255))
    create_time = Column(DateTime)
    update_time = Column(DateTime)


class GroupBuyOrderList(Base):
    __tablename__ = "group_buy_order_list"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(64), index=True)
    team_id = Column(String(16), index=True)
    order_id = Column(String(16), index=True)
    activity_id = Column(Integer, index=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    goods_id = Column(String(16), index=True)
    source = Column(String(8))
    channel = Column(String(8))
    original_price = Column(DECIMAL(10, 2))
    deduction_price = Column(DECIMAL(10, 2))
    status = Column(Integer)
    out_trade_no = Column(String(32))
    out_trade_time = Column(DateTime)
    biz_id = Column(String(64))
    create_time = Column(DateTime)
    update_time = Column(DateTime)


class ScSkuActivity(Base):
    __tablename__ = "sc_sku_activity"

    id = Column(Integer, primary_key=True)
    source = Column(String(8))
    channel = Column(String(8))
    activity_id = Column(Integer, index=True)
    goods_id = Column(String(16), index=True)
    create_time = Column(DateTime)
    update_time = Column(DateTime)


class CrowdTags(Base):
    __tablename__ = "crowd_tags"

    id = Column(Integer, primary_key=True)
    tag_id = Column(String(16), index=True)
    tag_name = Column(String(64))
    tag_desc = Column(String(255))
    statistics = Column(String(255))
    create_time = Column(DateTime)
    update_time = Column(DateTime)

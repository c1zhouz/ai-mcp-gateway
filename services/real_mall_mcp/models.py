from sqlalchemy import Column, String, Float, Integer, DateTime, DECIMAL
from database import Base
from datetime import datetime

class Sku(Base):
    __tablename__ = "sku"

    id = Column(Integer, primary_key=True)
    source = Column(String(8))
    channel = Column(String(8))
    goods_id = Column(String(16))
    goods_name = Column(String(128))
    original_price = Column(DECIMAL(10, 2))
    create_time = Column(DateTime)
    update_time = Column(DateTime)

class GroupBuyOrderList(Base):
    __tablename__ = "group_buy_order_list"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(64))
    team_id = Column(String(8))
    order_id = Column(String(12))
    activity_id = Column(Integer)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    goods_id = Column(String(16))
    source = Column(String(8))
    channel = Column(String(8))
    original_price = Column(DECIMAL(8, 2))
    deduction_price = Column(DECIMAL(8, 2))
    status = Column(Integer)
    out_trade_no = Column(String(12))
    out_trade_time = Column(DateTime)
    biz_id = Column(String(64))
    create_time = Column(DateTime)
    update_time = Column(DateTime)

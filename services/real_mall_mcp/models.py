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

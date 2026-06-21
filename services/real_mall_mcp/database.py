import os
from typing import Awaitable, Callable, TypeVar

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+aiomysql://root:123456@127.0.0.1:13306/group_buy_market",
)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()
T = TypeVar("T")


async def run_read_query(query: Callable[[AsyncSession], Awaitable[T]]) -> T:
    async with AsyncSessionLocal() as session:
        return await query(session)


async def get_db_session():
    async with AsyncSessionLocal() as session:
        yield session

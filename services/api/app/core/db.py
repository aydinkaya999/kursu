from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Database:
    def __init__(self, url: str) -> None:
        self.engine = create_async_engine(
            url, connect_args={"connect_timeout": 3}, pool_pre_ping=True, pool_timeout=3
        )
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def is_ready(self) -> bool:
        try:
            async with self.sessions() as session:
                await session.execute(text("SELECT 1"))
        except SQLAlchemyError:
            return False
        return True

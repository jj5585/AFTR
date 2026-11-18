from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from backend.app.core.config import settings


# Use TEST_DATABASE_URL if ENVIRONMENT is "test"
active_db_url = (
    settings.TEST_DATABASE_URL
    if settings.ENVIRONMENT == "test"
    else settings.DATABASE_URL
)

# SQLite in aiosqlite requires special handling for memory connection or relative paths
connect_args = {}
if active_db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_async_engine(
    active_db_url,
    echo=settings.DEBUG and settings.ENVIRONMENT != "test",
    future=True,
    connect_args=connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

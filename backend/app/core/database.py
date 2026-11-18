from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from backend.app.core.config import settings
from backend.app.models.base import Base

# Active database URL based on environment
active_db_url = (
    settings.TEST_DATABASE_URL
    if settings.ENVIRONMENT == "test"
    else settings.DATABASE_URL
)

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


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

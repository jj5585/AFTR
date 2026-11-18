import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_database_connection(db_session: AsyncSession):
    result = await db_session.execute(text("SELECT 1"))
    value = result.scalar()
    assert value == 1


@pytest.mark.asyncio
async def test_database_session_rollback_and_commit(db_session: AsyncSession):
    # Test session integrity
    result = await db_session.execute(text("SELECT 42 AS answer"))
    row = result.mappings().one()
    assert row["answer"] == 42

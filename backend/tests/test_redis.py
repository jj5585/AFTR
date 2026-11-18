import pytest
from unittest.mock import AsyncMock, patch
from backend.app.core.redis import check_redis_health, get_redis_client, close_redis_client


@pytest.mark.asyncio
async def test_redis_health_success():
    mock_client = AsyncMock()
    mock_client.ping.return_value = True

    with patch("backend.app.core.redis.get_redis_client", return_value=mock_client):
        result = await check_redis_health()
        assert result is True


@pytest.mark.asyncio
async def test_redis_health_failure():
    mock_client = AsyncMock()
    mock_client.ping.side_effect = ConnectionError("Could not connect to Redis")

    with patch("backend.app.core.redis.get_redis_client", return_value=mock_client):
        result = await check_redis_health()
        assert result is False


@pytest.mark.asyncio
async def test_close_redis_client():
    mock_client = AsyncMock()
    with patch("backend.app.core.redis.redis_client", mock_client):
        await close_redis_client()
        mock_client.close.assert_awaited_once()

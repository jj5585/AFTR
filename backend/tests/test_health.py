import pytest
from httpx import AsyncClient
from unittest.mock import patch


@pytest.mark.asyncio
async def test_root_endpoint(async_client: AsyncClient):
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "AFTR API"
    assert data["status"] == "online"
    assert "version" in data


@pytest.mark.asyncio
async def test_health_check_live_probe(async_client: AsyncClient):
    response = await async_client.get("/api/v1/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "timestamp_utc" in data


@pytest.mark.asyncio
async def test_health_check_comprehensive_all_healthy(async_client: AsyncClient):
    with patch("backend.app.api.v1.health.check_redis_health", return_value=True):
        response = await async_client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["services"]["api"] == "healthy"
        assert data["services"]["database"] == "connected"
        assert data["services"]["redis"] == "connected"
        assert "timestamp_utc" in data


@pytest.mark.asyncio
async def test_health_check_degraded_when_redis_down(async_client: AsyncClient):
    with patch("backend.app.api.v1.health.check_redis_health", return_value=False):
        response = await async_client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["services"]["redis"] == "disconnected"
        assert data["services"]["database"] == "connected"

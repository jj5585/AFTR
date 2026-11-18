import logging
from typing import Optional
from redis.asyncio import Redis, from_url
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

redis_client: Optional[Redis] = None


async def get_redis_client() -> Redis:
    global redis_client
    if redis_client is None:
        redis_client = from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return redis_client


async def close_redis_client():
    global redis_client
    if redis_client is not None:
        await redis_client.close()
        redis_client = None


async def check_redis_health() -> bool:
    try:
        client = await get_redis_client()
        response = await client.ping()
        return bool(response)
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        return False

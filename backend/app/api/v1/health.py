from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.redis import check_redis_health

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", status_code=status.HTTP_200_OK)
async def health_check(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Comprehensive health check for API, Database, and Redis connections.
    """
    # 1. Database Check
    db_status = False
    try:
        result = await db.execute(text("SELECT 1"))
        db_status = result.scalar() == 1
    except Exception:
        db_status = False

    # 2. Redis Check
    redis_status = await check_redis_health()

    overall_healthy = db_status and redis_status

    return {
        "status": "healthy" if overall_healthy else "degraded",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "services": {
            "api": "healthy",
            "database": "connected" if db_status else "disconnected",
            "redis": "connected" if redis_status else "disconnected",
        }
    }


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_probe() -> Dict[str, str]:
    """
    Simple liveness check for container orchestrators (k8s / docker / healthcheck).
    """
    return {
        "status": "alive",
        "timestamp_utc": datetime.now(timezone.utc).isoformat()
    }

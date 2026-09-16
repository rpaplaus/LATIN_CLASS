from typing import Any

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_redis_client

router = APIRouter()


@router.get("", response_model=None)
async def health_check(
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis_client),
) -> Any:
    """Comprehensive health check checking API, PostgreSQL and Redis connectivity."""
    db_status = "healthy"
    redis_status = "healthy"

    # Verify PostgreSQL connectivity
    try:
        result = await db.execute(text("SELECT 1"))
        if result.scalar() != 1:
            db_status = "unhealthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # Verify Redis connectivity
    try:
        pong = await redis.ping()
        if not pong:
            redis_status = "unhealthy"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"

    is_overall_healthy = (db_status == "healthy") and (redis_status == "healthy")
    response_payload = {
        "status": "ok" if is_overall_healthy else "degraded",
        "services": {
            "postgres": db_status,
            "redis": redis_status,
        },
    }

    status_code = (
        status.HTTP_200_OK
        if is_overall_healthy
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    return JSONResponse(status_code=status_code, content=response_payload)

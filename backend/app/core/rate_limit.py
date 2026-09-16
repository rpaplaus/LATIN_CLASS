import logging

import redis.asyncio as aioredis
from fastapi import HTTPException, Request, status

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_client_ip(request: Request) -> str:
    """Extract client IP address considering proxy headers."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"


async def check_rate_limit(
    redis: aioredis.Redis,
    request: Request,
    action: str,
    max_requests: int,
    window_seconds: int = 60,
) -> None:
    """Enforce rate limits per IP using an atomic Redis counter with TTL.

    Raises HTTP 429 Too Many Requests if the quota is exceeded.
    """
    if not settings.RATE_LIMIT_ENABLED:
        return

    client_ip = get_client_ip(request)
    redis_key = f"latin_rate_limit:{action}:{client_ip}"

    try:
        current_count = await redis.incr(redis_key)
        if current_count == 1:
            await redis.expire(redis_key, window_seconds)

        if current_count > max_requests:
            ttl = await redis.ttl(redis_key)
            retry_after = str(max(ttl, 1))
            logger.warning(
                "Rate limit exceeded for IP %s on action '%s' (%d/%d)",
                client_ip,
                action,
                current_count,
                max_requests,
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Muitas requisições. Por favor, aguarde antes de tentar novamente.",
                headers={"Retry-After": retry_after},
            )
    except HTTPException:
        raise
    except Exception as exc:
        # Fail open with warning if Redis has transient issues, ensuring service availability
        logger.error("Rate limiting check error: %s", exc)

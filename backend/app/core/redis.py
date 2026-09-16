from collections.abc import AsyncGenerator

import redis.asyncio as aioredis

from app.core.config import settings

redis_pool: aioredis.ConnectionPool | None = None


def init_redis_pool() -> aioredis.ConnectionPool:
    """Initialize Redis connection pool."""
    global redis_pool
    if redis_pool is None:
        redis_pool = aioredis.ConnectionPool.from_url(
            settings.async_redis_url,
            decode_responses=True,
            max_connections=20,
        )
    return redis_pool


async def close_redis_pool() -> None:
    """Close Redis connection pool."""
    global redis_pool
    if redis_pool is not None:
        await redis_pool.disconnect()
        redis_pool = None


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """Dependency to get an async Redis client instance."""
    pool = init_redis_pool()
    client = aioredis.Redis(connection_pool=pool)
    try:
        yield client
    finally:
        await client.aclose()


async def check_redis_health() -> bool:
    """Ping Redis to verify server connectivity."""
    try:
        pool = init_redis_pool()
        client = aioredis.Redis(connection_pool=pool)
        pong = await client.ping()
        await client.aclose()
        return bool(pong)
    except Exception:
        return False

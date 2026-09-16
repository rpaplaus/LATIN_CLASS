import asyncio
import contextlib
from collections.abc import AsyncGenerator

import redis.asyncio as aioredis

from app.core.config import settings

_redis_pool: aioredis.ConnectionPool | None = None
_pool_loop: asyncio.AbstractEventLoop | None = None


def get_redis_pool() -> aioredis.ConnectionPool:
    """Retrieve or initialize the global connection pool for Redis bound to the active loop."""
    global _redis_pool, _pool_loop
    current_loop: asyncio.AbstractEventLoop | None = None
    with contextlib.suppress(RuntimeError):
        current_loop = asyncio.get_running_loop()

    if _redis_pool is None or (
        _pool_loop is not None
        and current_loop is not None
        and _pool_loop is not current_loop
    ):
        _redis_pool = aioredis.ConnectionPool.from_url(
            settings.async_redis_url,
            decode_responses=True,
            max_connections=20,
        )
        _pool_loop = current_loop
    return _redis_pool


async def close_redis_pool() -> None:
    """Gracefully disconnect and release all connections in the pool."""
    global _redis_pool, _pool_loop
    if _redis_pool is not None:
        await _redis_pool.disconnect()
        _redis_pool = None
        _pool_loop = None


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """Dependency yielding an async Redis client backed by the global connection pool."""
    pool = get_redis_pool()
    client = aioredis.Redis(connection_pool=pool)
    try:
        yield client
    finally:
        await client.aclose()


async def check_redis_health() -> bool:
    """Ping Redis using the shared connection pool to verify connectivity."""
    try:
        pool = get_redis_pool()
        client = aioredis.Redis(connection_pool=pool)
        pong = await client.ping()
        await client.aclose()
        return bool(pong)
    except Exception:
        return False


async def store_refresh_token(
    redis: aioredis.Redis, user_id: str, jti: str, ttl_seconds: int
) -> None:
    """Store an active refresh token JTI with expiration TTL in Redis."""
    key = f"refresh_token:{user_id}:{jti}"
    await redis.set(key, "active", ex=ttl_seconds)


async def is_refresh_token_valid(redis: aioredis.Redis, user_id: str, jti: str) -> bool:
    """Check if a refresh token JTI is active and not revoked."""
    key = f"refresh_token:{user_id}:{jti}"
    value = await redis.get(key)
    return value == "active"


async def revoke_refresh_token(redis: aioredis.Redis, user_id: str, jti: str) -> None:
    """Revoke a specific refresh token by removing its JTI from Redis."""
    key = f"refresh_token:{user_id}:{jti}"
    await redis.delete(key)


async def mark_refresh_token_revoked(
    redis: aioredis.Redis, user_id: str, jti: str, ttl_seconds: int = 3600
) -> None:
    """Mark JTI as revoked and record it in blacklist for reuse detection."""
    key = f"refresh_token:{user_id}:{jti}"
    revoked_key = f"revoked_token:{user_id}:{jti}"
    await redis.delete(key)
    await redis.set(revoked_key, "revoked", ex=ttl_seconds)


async def is_refresh_token_reused(
    redis: aioredis.Redis, user_id: str, jti: str
) -> bool:
    """Check if a previously revoked JTI is being reused (indicates token theft)."""
    revoked_key = f"revoked_token:{user_id}:{jti}"
    value = await redis.get(revoked_key)
    return value == "revoked"


async def revoke_all_user_tokens(redis: aioredis.Redis, user_id: str) -> None:
    """Revoke all active refresh tokens for a given user."""
    pattern = f"refresh_token:{user_id}:*"
    async for key in redis.scan_iter(match=pattern):
        await redis.delete(key)

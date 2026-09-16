from collections.abc import AsyncGenerator

import redis.asyncio as aioredis

from app.core.config import settings


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """Dependency to get an async Redis client instance safely bound to current event loop."""
    client = aioredis.from_url(
        settings.async_redis_url,
        decode_responses=True,
    )
    try:
        yield client
    finally:
        await client.aclose()


async def check_redis_health() -> bool:
    """Ping Redis to verify server connectivity."""
    try:
        client = aioredis.from_url(
            settings.async_redis_url,
            decode_responses=True,
        )
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


async def revoke_all_user_tokens(redis: aioredis.Redis, user_id: str) -> None:
    """Revoke all active refresh tokens for a given user."""
    pattern = f"refresh_token:{user_id}:*"
    async for key in redis.scan_iter(match=pattern):
        await redis.delete(key)

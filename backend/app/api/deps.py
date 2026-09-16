import uuid
from collections.abc import AsyncGenerator

import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.redis import get_redis
from app.core.security import decode_token
from app.models.user import User

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injecting an async database session."""
    async for session in get_db_session():
        yield session


async def get_redis_client() -> AsyncGenerator[aioredis.Redis, None]:
    """Dependency injecting an async Redis client."""
    async for client in get_redis():
        yield client


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(reusable_oauth2),
) -> User:
    """Validate Bearer token and retrieve the corresponding active user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_uuid = uuid.UUID(user_id_str)
    except (ValueError, TypeError):
        raise credentials_exception from None

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    return user


async def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """Verify that current authenticated user is a superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user

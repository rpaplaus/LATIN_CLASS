import uuid
from typing import Annotated, Any

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_redis_client
from app.core.config import settings
from app.core.redis import (
    is_refresh_token_valid,
    revoke_refresh_token,
    store_refresh_token,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.schemas.token import RefreshTokenRequest, Token
from app.schemas.user import UserCreate, UserResponse

router = APIRouter()


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Register a new student account."""
    query = select(User).where(User.email == user_in.email)
    result = await db.execute(query)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists in the system.",
        )

    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis_client),
) -> Token:
    """OAuth2 compatible token login, issuing Access and Refresh Tokens."""
    query = select(User).where(User.email == form_data.username)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    # 1. Create Access Token
    access_token = create_access_token(subject=str(user.id))

    # 2. Create Refresh Token with unique JTI
    refresh_token, jti = create_refresh_token(subject=str(user.id))

    # 3. Persist JTI in Redis with TTL
    refresh_ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
    await store_refresh_token(redis, str(user.id), jti, ttl_seconds=refresh_ttl)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis_client),
) -> Token:
    """Rotate Refresh Token and issue new Access + Refresh Token pair."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(body.refresh_token)
    if payload is None:
        raise credentials_exception

    if payload.get("type") != "refresh":
        raise credentials_exception

    user_id_str = payload.get("sub")
    jti = payload.get("jti")
    if not user_id_str or not jti:
        raise credentials_exception

    # Check if this JTI is still active in Redis
    is_valid = await is_refresh_token_valid(redis, user_id_str, jti)
    if not is_valid:
        raise credentials_exception

    # Verify user existence and active status
    try:
        user_uuid = uuid.UUID(user_id_str)
    except (ValueError, TypeError):
        raise credentials_exception from None

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise credentials_exception

    # Refresh Token Rotation (RTR): Revoke previous JTI
    await revoke_refresh_token(redis, user_id_str, jti)

    # Issue new pair
    new_access_token = create_access_token(subject=str(user.id))
    new_refresh_token, new_jti = create_refresh_token(subject=str(user.id))

    refresh_ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
    await store_refresh_token(redis, str(user.id), new_jti, ttl_seconds=refresh_ttl)

    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout")
async def logout(
    body: RefreshTokenRequest,
    redis: aioredis.Redis = Depends(get_redis_client),
) -> Any:
    """Revoke user session by invalidating the refresh token."""
    payload = decode_token(body.refresh_token)
    if payload:
        user_id_str = payload.get("sub")
        jti = payload.get("jti")
        if user_id_str and jti:
            await revoke_refresh_token(redis, user_id_str, jti)

    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def read_current_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current authenticated user profile."""
    return current_user

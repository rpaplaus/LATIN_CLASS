from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_superuser, get_current_user, get_db
from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate

router = APIRouter()


@router.get("/", response_model=list[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_superuser),
) -> Any:
    """Retrieve users list (Admin only)."""
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    """Update current user profile information."""
    if user_in.email is not None and user_in.email != current_user.email:
        query = select(User).where(User.email == user_in.email)
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered by another account.",
            )
        current_user.email = user_in.email

    if user_in.full_name is not None:
        current_user.full_name = user_in.full_name

    if user_in.password is not None:
        current_user.hashed_password = get_password_hash(user_in.password)

    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user

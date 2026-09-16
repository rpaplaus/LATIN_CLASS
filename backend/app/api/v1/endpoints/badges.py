import logging

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db
from app.models.gamification import Badge, UserBadge
from app.models.user import User
from app.schemas.gamification import (
    BadgeRead,
    SenateBadgeItem,
    SenateBadgesOverviewResponse,
    UserBadgeRead,
)
from app.services.gamification import get_user_senate_overview

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=list[BadgeRead])
async def list_all_badges(
    db: AsyncSession = Depends(get_db),
) -> list[BadgeRead]:
    """Retrieve all canonical Roman Senate honors and badges."""
    stmt = select(Badge).order_by(Badge.tier, Badge.requirement_value)
    badges = (await db.execute(stmt)).scalars().all()
    return [BadgeRead.model_validate(b) for b in badges]


@router.get("/me", response_model=list[UserBadgeRead])
async def list_my_badges(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[UserBadgeRead]:
    """Retrieve all Roman honors currently unlocked by the authenticated student."""
    stmt = (
        select(UserBadge)
        .where(UserBadge.user_id == current_user.id)
        .options(selectinload(UserBadge.badge))
        .order_by(UserBadge.unlocked_at.desc())
    )
    user_badges = (await db.execute(stmt)).scalars().all()
    return [UserBadgeRead.model_validate(ub) for ub in user_badges]


@router.get("/overview", response_model=SenateBadgesOverviewResponse)
async def get_senate_hall_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SenateBadgesOverviewResponse:
    """Retrieve full Senate Hall gallery overview with student's earned and locked badges."""
    unlocked_count, total_count, items = await get_user_senate_overview(
        db=db,
        user_id=current_user.id,
    )
    pct = (unlocked_count / total_count * 100.0) if total_count > 0 else 0.0

    return SenateBadgesOverviewResponse(
        total_unlocked=unlocked_count,
        total_available=total_count,
        completion_percentage=round(pct, 1),
        badges=[SenateBadgeItem.model_validate(item) for item in items],
    )

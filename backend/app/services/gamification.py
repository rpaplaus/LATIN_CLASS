import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gamification import Badge, UserBadge
from app.models.progress import LessonCompletion, UserProgress

logger = logging.getLogger(__name__)


_canonic_badges_cache: list[Badge] | None = None


async def get_canonic_badges(db: AsyncSession) -> list[Badge]:
    """Retrieve all canonical Roman Senate badges with in-memory caching."""
    global _canonic_badges_cache
    if _canonic_badges_cache is None:
        all_badges_stmt = select(Badge).order_by(Badge.tier, Badge.requirement_value)
        _canonic_badges_cache = list(
            (await db.execute(all_badges_stmt)).scalars().all()
        )
    return _canonic_badges_cache


def invalidate_badges_cache() -> None:
    """Invalidate canonic badges cache upon administrative updates."""
    global _canonic_badges_cache
    _canonic_badges_cache = None


async def evaluate_and_award_badges(
    db: AsyncSession,
    user_id: uuid.UUID,
    trigger_event: str,
    context: dict[str, Any] | None = None,
) -> list[Badge]:
    """Evaluate student progress against Roman Senate badge criteria and award newly earned honors."""
    ctx = context or {}

    # 1. Fetch user progress
    prog_stmt = select(UserProgress).where(UserProgress.user_id == user_id)
    progress = (await db.execute(prog_stmt)).scalar_one_or_none()
    if not progress:
        return []

    # 2. Fetch already unlocked badge IDs for user
    unlocked_stmt = select(UserBadge.badge_id).where(UserBadge.user_id == user_id)
    unlocked_ids = set((await db.execute(unlocked_stmt)).scalars().all())

    # 3. Fetch all canonic badges (Cached)
    all_badges = await get_canonic_badges(db)

    # 4. Check highest score in completions if needed
    has_perfect_score = ctx.get("score", 0) >= 100
    if not has_perfect_score:
        score_check = await db.execute(
            select(LessonCompletion).where(
                LessonCompletion.user_id == user_id,
                LessonCompletion.score >= 100,
            )
        )
        if score_check.first():
            has_perfect_score = True

    newly_awarded: list[Badge] = []

    for b in all_badges:
        if b.id in unlocked_ids:
            continue

        qualified = False

        if b.requirement_type == "lessons_count":
            qualified = progress.completed_lessons_count >= b.requirement_value

        elif b.requirement_type == "min_streak":
            qualified = progress.current_streak_days >= b.requirement_value

        elif b.requirement_type == "perfect_score":
            qualified = has_perfect_score

        elif b.requirement_type == "total_points":
            qualified = progress.total_points >= b.requirement_value

        elif b.requirement_type == "module_complete":
            # If 3 or more lessons completed (or explicitly signaled)
            qualified = bool(
                ctx.get("module_complete") or progress.completed_lessons_count >= 3
            )

        elif b.requirement_type == "library_search":
            qualified = trigger_event == "library_search" or bool(
                ctx.get("library_search")
            )

        if qualified:
            user_badge = UserBadge(
                user_id=user_id,
                badge_id=b.id,
                metadata_={
                    "trigger_event": trigger_event,
                    "completed_lessons": progress.completed_lessons_count,
                    "streak_days": progress.current_streak_days,
                },
            )
            db.add(user_badge)
            progress.total_points += b.xp_reward
            newly_awarded.append(b)
            unlocked_ids.add(b.id)
            logger.info(
                "Awarded Roman Senate Badge '%s' to user %s (XP +%d)",
                b.title,
                user_id,
                b.xp_reward,
            )

    if newly_awarded:
        await db.commit()

    return newly_awarded


async def get_user_senate_overview(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> tuple[int, int, list[dict[str, Any]]]:
    """Retrieve full Roman Senate honors catalogue mapped with student's unlock status."""
    # 1. Fetch user progress
    prog_stmt = select(UserProgress).where(UserProgress.user_id == user_id)
    progress = (await db.execute(prog_stmt)).scalar_one_or_none()
    streak = progress.current_streak_days if progress else 0
    lessons_done = progress.completed_lessons_count if progress else 0
    points = progress.total_points if progress else 0

    # 2. Fetch all badges from cache
    all_badges = await get_canonic_badges(db)

    # 3. Fetch user's unlocked badges
    user_badges_stmt = select(UserBadge).where(UserBadge.user_id == user_id)
    user_badges = (await db.execute(user_badges_stmt)).scalars().all()
    unlocked_map = {ub.badge_id: ub for ub in user_badges}

    items: list[dict[str, Any]] = []
    for b in all_badges:
        ub = unlocked_map.get(b.id)
        is_unlocked = ub is not None

        # Calculate current progress toward requirement
        cur_prog = 0
        if b.requirement_type == "lessons_count":
            cur_prog = min(lessons_done, b.requirement_value)
        elif b.requirement_type == "min_streak":
            cur_prog = min(streak, b.requirement_value)
        elif b.requirement_type == "total_points":
            cur_prog = min(points, b.requirement_value)
        elif is_unlocked:
            cur_prog = b.requirement_value

        items.append(
            {
                "badge": b,
                "is_unlocked": is_unlocked,
                "unlocked_at": ub.unlocked_at if ub else None,
                "progress": cur_prog,
            }
        )

    return len(unlocked_map), len(all_badges), items

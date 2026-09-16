import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gamification import Badge, UserBadge
from app.models.progress import UserProgress
from app.models.user import User
from app.services.gamification import (
    evaluate_and_award_badges,
)


@pytest.mark.asyncio
async def test_canonical_badges_seeded(db_session: AsyncSession) -> None:
    """Verify all 7 Roman Senate badges are properly seeded in the database."""
    stmt = select(Badge)
    badges = (await db_session.execute(stmt)).scalars().all()
    assert len(badges) >= 7

    codes = {b.code for b in badges}
    assert "TIRO_PRIMUS" in codes
    assert "CENTURIO_STREAK_3" in codes
    assert "LEGATUS_STREAK_7" in codes
    assert "CENSOR_SEVERUS" in codes
    assert "SENATOR_MODULE_1" in codes
    assert "SCRIBA_BIBLIOTHECA" in codes
    assert "IMPERATOR_LATIUM" in codes


@pytest.mark.asyncio
async def test_evaluate_and_award_first_lesson_badge(
    db_session: AsyncSession,
    test_user: User,
) -> None:
    """Verify TIRO_PRIMUS is awarded when student completes 1 lesson."""
    # Setup initial progress with 1 completed lesson
    prog = UserProgress(
        user_id=test_user.id,
        completed_lessons_count=1,
        total_points=100,
        current_streak_days=1,
    )
    db_session.add(prog)
    await db_session.commit()

    # Evaluate badges
    new_badges = await evaluate_and_award_badges(
        db=db_session,
        user_id=test_user.id,
        trigger_event="complete_lesson",
    )
    assert len(new_badges) >= 1
    new_codes = {b.code for b in new_badges}
    assert "TIRO_PRIMUS" in new_codes

    # Verify UserBadge saved in DB
    user_badges_stmt = select(UserBadge).where(UserBadge.user_id == test_user.id)
    ub_list = (await db_session.execute(user_badges_stmt)).scalars().all()
    assert len(ub_list) >= 1

    # Idempotency: re-running should award 0 new badges
    repeat = await evaluate_and_award_badges(
        db=db_session,
        user_id=test_user.id,
        trigger_event="complete_lesson",
    )
    assert len(repeat) == 0


@pytest.mark.asyncio
async def test_evaluate_and_award_streak_and_censor_badges(
    db_session: AsyncSession,
    test_user: User,
) -> None:
    """Verify streak badge and Censor Severus badge (score 100) are awarded."""
    prog = UserProgress(
        user_id=test_user.id,
        completed_lessons_count=3,
        total_points=300,
        current_streak_days=3,
    )
    db_session.add(prog)
    await db_session.commit()

    new_badges = await evaluate_and_award_badges(
        db=db_session,
        user_id=test_user.id,
        trigger_event="censor_evaluation",
        context={"score": 100},
    )
    new_codes = {b.code for b in new_badges}
    assert "CENTURIO_STREAK_3" in new_codes
    assert "CENSOR_SEVERUS" in new_codes


@pytest.mark.asyncio
async def test_badges_endpoints(
    client: AsyncClient,
    test_user: User,
    db_session: AsyncSession,
) -> None:
    """Verify GET /api/v1/badges, /badges/me and /badges/overview endpoints."""
    from app.core.security import create_access_token

    token = create_access_token(subject=str(test_user.id))
    auth_headers = {"Authorization": f"Bearer {token}"}

    # 1. List all badges
    all_resp = await client.get("/api/v1/badges/")
    assert all_resp.status_code == 200
    all_data = all_resp.json()
    assert len(all_data) >= 7

    # 2. List user badges before earning any
    me_resp1 = await client.get("/api/v1/badges/me", headers=auth_headers)
    assert me_resp1.status_code == 200
    assert len(me_resp1.json()) == 0

    # 3. Award a badge to test_user
    prog = UserProgress(
        user_id=test_user.id,
        completed_lessons_count=1,
        total_points=50,
        current_streak_days=1,
    )
    db_session.add(prog)
    await db_session.commit()
    await evaluate_and_award_badges(db_session, test_user.id, "complete_lesson")

    # 4. List user badges after earning TIRO_PRIMUS
    me_resp2 = await client.get("/api/v1/badges/me", headers=auth_headers)
    assert me_resp2.status_code == 200
    me_data = me_resp2.json()
    assert len(me_data) >= 1
    assert me_data[0]["badge"]["code"] == "TIRO_PRIMUS"

    # 5. Get Senate Hall overview
    ov_resp = await client.get("/api/v1/badges/overview", headers=auth_headers)
    assert ov_resp.status_code == 200
    ov_data = ov_resp.json()
    assert ov_data["total_unlocked"] >= 1
    assert ov_data["total_available"] >= 7
    assert ov_data["completion_percentage"] > 0
    assert len(ov_data["badges"]) >= 7

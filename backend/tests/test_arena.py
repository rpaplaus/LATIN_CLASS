from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.progress import StudentTopicProficiency
from app.models.user import User


@pytest.mark.asyncio
async def test_arena_selects_lowest_mastery_topic(
    client: AsyncClient,
    test_user: User,
    db_session: AsyncSession,
) -> None:
    """Arena engine must automatically select the student's most vulnerable topic."""
    token = create_access_token(subject=str(test_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a mastered topic
    topic_strong = StudentTopicProficiency(
        user_id=test_user.id,
        topic_key="1st_declension_nominative",
        category="morphology",
        mastery_score=0.85,
        attempts_count=6,
        correct_count=5,
        consecutive_successes=3,
        weakness_flags=[],
        last_evaluated_at=datetime.now(UTC),
    )
    # 2. Create a vulnerable topic (EMA = 0.32)
    topic_weak = StudentTopicProficiency(
        user_id=test_user.id,
        topic_key="1st_declension_accusative",
        category="syntax",
        mastery_score=0.32,
        attempts_count=4,
        correct_count=1,
        consecutive_successes=0,
        weakness_flags=["desinencia_am"],
        last_evaluated_at=datetime.now(UTC),
    )
    db_session.add_all([topic_strong, topic_weak])
    await db_session.commit()

    # Call /arena/generate without specifying topic
    response = await client.post(
        "/api/v1/arena/generate",
        json={"topic_key": None},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()

    assert data["topic_key"] == "1st_declension_accusative"
    assert data["current_mastery"] == 0.32
    assert data["vulnerability_score"] == 0.68
    assert len(data["cards"]) == 3

    for card in data["cards"]:
        assert "latin" in card and len(card["latin"]) > 0
        assert "translation" in card and len(card["translation"]) > 0
        assert "audio_url" in card and "/api/v1/media/audio/" in card["audio_url"]


@pytest.mark.asyncio
async def test_arena_evaluation_exact_match_and_ema_increase(
    client: AsyncClient,
    test_user: User,
    db_session: AsyncSession,
) -> None:
    """A correct translation in the Arena must increase student's EMA mastery score in real-time."""
    token = create_access_token(subject=str(test_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    # Setup baseline topic proficiency
    prof = StudentTopicProficiency(
        user_id=test_user.id,
        topic_key="verb_esse_present",
        category="verbs",
        mastery_score=0.40,
        attempts_count=2,
        correct_count=1,
        consecutive_successes=0,
        weakness_flags=[],
        last_evaluated_at=datetime.now(UTC),
    )
    db_session.add(prof)
    await db_session.commit()

    # Submit exact matching translation
    eval_payload = {
        "topic_key": "verb_esse_present",
        "card_id": 1,
        "latin": "Marcus servus non est.",
        "expected_answer": "Marco não é um escravo.",
        "student_answer": "Marco não é um escravo.",
    }
    response = await client.post(
        "/api/v1/arena/evaluate",
        json=eval_payload,
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()

    assert data["is_correct"] is True
    assert data["score"] == 100
    assert data["previous_mastery"] == 0.40
    # EMA formula: 0.40 + 0.20 * (1.0 - 0.40) = 0.52
    assert data["new_mastery"] > data["previous_mastery"]
    assert data["new_mastery"] >= 0.50


@pytest.mark.asyncio
async def test_arena_evaluation_error_and_ema_penalty(
    client: AsyncClient,
    test_user: User,
    db_session: AsyncSession,
) -> None:
    """An incorrect answer must penalize EMA mastery score and record weakness flags."""
    token = create_access_token(subject=str(test_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    prof = StudentTopicProficiency(
        user_id=test_user.id,
        topic_key="2nd_declension_masculine",
        category="morphology",
        mastery_score=0.60,
        attempts_count=3,
        correct_count=2,
        consecutive_successes=2,
        weakness_flags=[],
        last_evaluated_at=datetime.now(UTC),
    )
    db_session.add(prof)
    await db_session.commit()

    eval_payload = {
        "topic_key": "2nd_declension_masculine",
        "card_id": 2,
        "latin": "Dominus servum vocat.",
        "expected_answer": "O senhor chama o escravo.",
        "student_answer": "O gato dorme na cama.",  # Completely wrong
    }
    response = await client.post(
        "/api/v1/arena/evaluate",
        json=eval_payload,
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()

    assert data["is_correct"] is False
    assert data["previous_mastery"] == 0.60
    assert data["new_mastery"] < data["previous_mastery"]

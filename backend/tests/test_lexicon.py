import uuid
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.course import CourseModule, Lesson
from app.models.progress import LessonCompletion, UserVocabularyFavorite
from app.models.user import User


@pytest.mark.asyncio
async def test_get_lexicon_empty_when_no_completed_lessons(
    client: AsyncClient,
    test_user: User,
) -> None:
    """A user with no completed lessons receives an empty lexicon with 200 OK."""
    token = create_access_token(subject=str(test_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/users/me/lexicon", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_words"] == 0
    assert data["favorite_count"] == 0
    assert data["entries"] == []
    assert data["available_classes"] == []


@pytest.mark.asyncio
async def test_lexicon_aggregation_deduplication_and_zero_llm(
    client: AsyncClient,
    test_user: User,
    db_session: AsyncSession,
) -> None:
    """Verifies that vocabulary from completed lessons is consolidated, deduplicated,

    and resolved with audio_url with ZERO LLM calls.
    """
    token = create_access_token(subject=str(test_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Module
    module = CourseModule(
        order_index=90,
        title="Módulo de Teste Lexicon",
        description="Módulo para validação do Lexicon Universale",
        level="beginner",
        is_published=True,
    )
    db_session.add(module)
    await db_session.flush()

    # 2. Create Lesson 1 with vocabulary
    lesson1 = Lesson(
        module_id=module.id,
        order_index=1,
        title="Lição Lexicon 1",
        pedagogical_objective="Testar vocabulário básico",
        grammar_topics=["Substantivos", "Verbos"],
        content={
            "lesson_id": str(uuid.uuid4()),
            "module_title": module.title,
            "lesson_title": "Lição Lexicon 1",
            "pedagogical_goal": "Goal 1",
            "historical_context": "Context 1",
            "theory_sections": [],
            "examples": [],
            "vocabulary": [
                {
                    "word": "puella",
                    "dictionary_entry": "puella, -ae, f.",
                    "grammatical_class": "Substantivo",
                    "translation": "menina, garota",
                    "example_sentence": "Puella cantat.",
                },
                {
                    "word": "amare",
                    "dictionary_entry": "amo, -are, -avi, -atum",
                    "grammatical_class": "Verbo",
                    "translation": "amar",
                    "example_sentence": "Puella patriam amat.",
                },
            ],
            "exercises": [],
            "teacher_tip": "Tip 1",
            "historical_trivia": [],
        },
    )
    db_session.add(lesson1)
    await db_session.flush()

    # 3. Create Lesson 2 with repeated word 'puella' and new word 'insula'
    lesson2 = Lesson(
        module_id=module.id,
        order_index=2,
        title="Lição Lexicon 2",
        pedagogical_objective="Testar desduplicação",
        grammar_topics=["Geografia"],
        content={
            "lesson_id": str(uuid.uuid4()),
            "module_title": module.title,
            "lesson_title": "Lição Lexicon 2",
            "pedagogical_goal": "Goal 2",
            "historical_context": "Context 2",
            "theory_sections": [],
            "examples": [],
            "vocabulary": [
                {
                    "word": "puella",  # Duplicate! Must be filtered out.
                    "dictionary_entry": "puella, -ae, f.",
                    "grammatical_class": "Substantivo",
                    "translation": "menina",
                    "example_sentence": "Puella in horto est.",
                },
                {
                    "word": "insula",
                    "dictionary_entry": "insula, -ae, f.",
                    "grammatical_class": "Substantivo",
                    "translation": "ilha, quarteirão",
                    "example_sentence": "Sicilia insula magna est.",
                },
            ],
            "exercises": [],
            "teacher_tip": "Tip 2",
            "historical_trivia": [],
        },
    )
    db_session.add(lesson2)
    await db_session.flush()

    # 4. Mark both lessons as completed by test_user
    comp1 = LessonCompletion(user_id=test_user.id, lesson_id=lesson1.id, score=100)
    comp2 = LessonCompletion(user_id=test_user.id, lesson_id=lesson2.id, score=95)
    db_session.add_all([comp1, comp2])

    # 5. Pre-favorite one word ('amare') in Pugillares
    fav = UserVocabularyFavorite(user_id=test_user.id, word="amare")
    db_session.add(fav)
    await db_session.commit()

    # 6. Call endpoint while mocking any potential LLM agent to prove ZERO LLM calls
    with patch("app.agent.llm_factory.get_llm_for_role") as mock_llm_role:
        response = await client.get("/api/v1/users/me/lexicon", headers=headers)
        assert response.status_code == 200
        mock_llm_role.assert_not_called()



    data = response.json()
    assert data["total_words"] == 3  # puella, amare, insula (puella was deduplicated!)
    assert data["favorite_count"] == 1

    words_in_response = [entry["word"] for entry in data["entries"]]
    assert words_in_response == ["puella", "amare", "insula"]

    # Verify audio_url is properly generated
    for entry in data["entries"]:
        assert "/api/v1/media/audio/" in entry["audio_url"]

    # Verify is_favorite flag
    amare_entry = next(e for e in data["entries"] if e["word"] == "amare")
    assert amare_entry["is_favorite"] is True

    puella_entry = next(e for e in data["entries"] if e["word"] == "puella")
    assert puella_entry["is_favorite"] is False


@pytest.mark.asyncio
async def test_toggle_vocabulary_favorite_pugillares(
    client: AsyncClient,
    test_user: User,
) -> None:
    """Test toggling vocabulary favorite on and off (Pugillares)."""
    token = create_access_token(subject=str(test_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Favorite 'gladius'
    resp1 = await client.post(
        "/api/v1/users/me/lexicon/favorites/toggle",
        json={"word": "gladius"},
        headers=headers,
    )
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["word"] == "gladius"
    assert data1["is_favorite"] is True

    # 2. Verify gladius is in favorites list
    list_resp = await client.get(
        "/api/v1/users/me/lexicon/favorites",
        headers=headers,
    )
    assert list_resp.status_code == 200
    favorites = list_resp.json()
    assert "gladius" in favorites

    # 3. Toggle again -> Unfavorite 'gladius'
    resp2 = await client.post(
        "/api/v1/users/me/lexicon/favorites/toggle",
        json={"word": "GLADIUS"},  # Case insensitive test
        headers=headers,
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["word"] == "gladius"
    assert data2["is_favorite"] is False

    # 4. Verify gladius is no longer in favorites list
    list_resp2 = await client.get(
        "/api/v1/users/me/lexicon/favorites",
        headers=headers,
    )
    assert list_resp2.status_code == 200
    assert "gladius" not in list_resp2.json()

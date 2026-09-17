import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.user import User


@pytest.mark.asyncio
async def test_list_course_modules(client: AsyncClient, test_user: User) -> None:
    """Test retrieving course syllabus with modules and lessons."""
    token = create_access_token(subject=str(test_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/lessons/modules", headers=headers)
    assert response.status_code == 200
    modules = response.json()
    assert len(modules) >= 2

    mod1 = modules[0]
    assert "Módulo I" in mod1["title"]
    assert len(mod1["lessons"]) >= 2
    assert mod1["lessons"][0]["is_completed"] is False


@pytest.mark.asyncio
async def test_get_initial_student_progress(
    client: AsyncClient, test_user: User
) -> None:
    """Test initializing student progress pointing to Module 1, Lesson 1."""
    token = create_access_token(subject=str(test_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/lessons/progress", headers=headers)
    assert response.status_code == 200
    progress = response.json()
    assert progress["user_id"] == str(test_user.id)
    assert progress["completed_lessons_count"] == 0
    assert progress["total_points"] == 0
    assert progress["current_lesson_title"] is not None


@pytest.mark.asyncio
async def test_generate_next_lesson_content(
    client: AsyncClient, test_user: User
) -> None:
    """Test Magister Latium generating structured lesson content."""
    token = create_access_token(subject=str(test_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.post("/api/v1/lessons/next", headers=headers)
    assert response.status_code == 200
    content = response.json()

    # Verify structured lesson content
    assert "lesson_id" in content
    assert "module_title" in content
    assert "lesson_title" in content
    assert "pedagogical_goal" in content
    assert "historical_context" in content

    # Verify theory sections
    assert len(content["theory_sections"]) >= 1
    assert "rule_summary" in content["theory_sections"][0]

    # Verify Latin examples
    assert len(content["examples"]) >= 1
    assert "latin" in content["examples"][0]
    assert "translation" in content["examples"][0]

    # Verify vocabulary
    assert len(content["vocabulary"]) >= 1
    assert "dictionary_entry" in content["vocabulary"][0]

    # Verify exercises
    assert len(content["exercises"]) >= 1
    assert "question" in content["exercises"][0]
    assert "correct_answer" in content["exercises"][0]
    assert "explanation" in content["exercises"][0]

    # Verify teacher tip
    assert "teacher_tip" in content


@pytest.mark.asyncio
async def test_complete_lesson_and_advance(
    client: AsyncClient, test_user: User
) -> None:
    """Test completing a lesson, gaining points and advancing syllabus."""
    token = create_access_token(subject=str(test_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Fetch current progress
    prog_resp = await client.get("/api/v1/lessons/progress", headers=headers)
    assert prog_resp.status_code == 200
    initial_progress = prog_resp.json()
    current_lesson_id = initial_progress["current_lesson_id"]
    assert current_lesson_id is not None

    # 2. Complete current lesson with score 90
    complete_resp = await client.post(
        f"/api/v1/lessons/{current_lesson_id}/complete",
        json={"score": 90},
        headers=headers,
    )
    assert complete_resp.status_code == 200
    updated_progress = complete_resp.json()
    assert updated_progress["completed_lessons_count"] == 1
    # 90 lesson points + 50 XP bonus from unlocked TIRO_PRIMUS badge = 140
    assert updated_progress["total_points"] >= 90
    assert updated_progress["current_lesson_id"] != current_lesson_id

    # 3. Check modules endpoint to verify lesson is marked completed
    modules_resp = await client.get("/api/v1/lessons/modules", headers=headers)
    assert modules_resp.status_code == 200
    modules = modules_resp.json()
    first_lesson = modules[0]["lessons"][0]
    assert str(first_lesson["id"]) == current_lesson_id
    assert first_lesson["is_completed"] is True


@pytest.mark.asyncio
async def test_lesson_progression_loop_fix_and_mastery(
    client: AsyncClient, test_user: User
) -> None:
    """Verify that completing Lesson 1 advances to Lesson 2 without repeating content, and global mastery is ~1%-20% (not 50%+)."""
    token = create_access_token(subject=str(test_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Initial proficiency: brand new user has 0% overall mastery
    prof_init = await client.get("/api/v1/users/me/proficiency", headers=headers)
    assert prof_init.status_code == 200
    assert prof_init.json()["overall_mastery"] == 0.0

    # 2. First lesson generation: must be Lesson 1 (Capítulo I)
    next_resp_1 = await client.post("/api/v1/lessons/next", headers=headers)
    assert next_resp_1.status_code == 200
    lesson_1_data = next_resp_1.json()
    assert "Nominativo" in lesson_1_data["lesson_title"]

    # 3. Complete Lesson 1
    complete_resp = await client.post(
        f"/api/v1/lessons/{lesson_1_data['lesson_id']}/complete",
        json={"score": 100},
        headers=headers,
    )
    assert complete_resp.status_code == 200
    prog_after = complete_resp.json()
    assert prog_after["completed_lessons_count"] == 1
    assert prog_after["current_lesson_id"] != lesson_1_data["lesson_id"]

    # 4. Next lesson generation: MUST generate Lesson 2 (Capítulo II), NOT repeat Lesson 1
    next_resp_2 = await client.post("/api/v1/lessons/next", headers=headers)
    assert next_resp_2.status_code == 200
    lesson_2_data = next_resp_2.json()
    assert lesson_2_data["lesson_id"] != lesson_1_data["lesson_id"]
    assert "Acusativo" in lesson_2_data["lesson_title"] or "Familia" in lesson_2_data["lesson_title"]

    # 5. Check global mastery: must NOT be inflated to 50%+
    # Canonical curriculum has 12-13 topics.
    prof_after = await client.get("/api/v1/users/me/proficiency", headers=headers)
    assert prof_after.status_code == 200
    mastery = prof_after.json()["overall_mastery"]
    assert 0.01 <= mastery < 0.30
    assert mastery < 0.50  # Must NEVER be 50%+ after just one lesson!


@pytest.mark.asyncio
async def test_exercise_evaluation_strict_topic_binding_and_no_ghosts(
    client: AsyncClient, test_user: User
) -> None:
    """Verify that evaluating an exercise updates canonical topics (e.g. 1st_declension_nominative) and never creates 'general_latin_syntax'."""
    token = create_access_token(subject=str(test_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Get current lesson
    prog_resp = await client.get("/api/v1/lessons/progress", headers=headers)
    lesson_id = prog_resp.json()["current_lesson_id"]
    assert lesson_id is not None

    # 2. Evaluate exercise via /exercises/evaluate endpoint
    eval_payload = {
        "lesson_id": lesson_id,
        "exercise_id": 1,
        "question": "Onde fica Roma?",
        "expected_answer": "Roma in Italia est",
        "student_answer": "Roma in Italia est",
        "exercise_type": "translation",
    }
    eval_resp = await client.post(
        f"/api/v1/lessons/{lesson_id}/exercises/evaluate",
        json=eval_payload,
        headers=headers,
    )
    assert eval_resp.status_code == 200
    assert eval_resp.json()["is_correct"] is True

    # 3. Inspect proficiency profile
    prof_resp = await client.get("/api/v1/users/me/proficiency", headers=headers)
    assert prof_resp.status_code == 200
    prof_data = prof_resp.json()

    topic_keys_in_profile = [t["topic_key"] for t in prof_data["topic_details"]]

    # Assert NO ghost topic was created
    assert "general_latin_syntax" not in topic_keys_in_profile

    # Assert canonical topics received attempts
    topic_map = {t["topic_key"]: t for t in prof_data["topic_details"]}
    assert "1st_declension_nominative" in topic_map
    assert topic_map["1st_declension_nominative"]["attempts_count"] >= 1
    assert topic_map["1st_declension_nominative"]["mastery_score"] > 0.0


@pytest.mark.asyncio
async def test_tabularium_history_and_zero_llm_lesson_by_id(
    client: AsyncClient, test_user: User, db_session: AsyncSession
) -> None:
    """Verify Tabularium history lists completed lessons and retrieves full content without LLM."""
    token = create_access_token(subject=str(test_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Fetch history via /history
    hist_resp = await client.get("/api/v1/lessons/history", headers=headers)
    assert hist_resp.status_code == 200
    initial_history = hist_resp.json()
    assert isinstance(initial_history, list)

    # 2. Get current lesson
    prog_resp = await client.get("/api/v1/lessons/progress", headers=headers)
    current_lesson_id = prog_resp.json()["current_lesson_id"]

    # 3. Complete lesson with score 95
    comp_resp = await client.post(
        f"/api/v1/lessons/{current_lesson_id}/complete",
        json={"score": 95},
        headers=headers,
    )
    assert comp_resp.status_code == 200

    # 4. Tabularium /history must list completed lesson with score and module
    hist_after = await client.get("/api/v1/lessons/history", headers=headers)
    assert hist_after.status_code == 200
    history_items = hist_after.json()
    assert len(history_items) >= 1
    item = next(h for h in history_items if h["id"] == current_lesson_id)
    assert item["score"] == 95
    assert item["module_title"] is not None
    assert "completed_at" in item

    # Also test /api/v1/lessons alias
    alias_resp = await client.get("/api/v1/lessons", headers=headers)
    assert alias_resp.status_code == 200
    assert len(alias_resp.json()) == len(history_items)

    # 5. Retrieve specific lesson content via GET /api/v1/lessons/{id} (Zero LLM cost)
    lesson_resp = await client.get(
        f"/api/v1/lessons/{current_lesson_id}", headers=headers
    )
    assert lesson_resp.status_code == 200
    lesson_data = lesson_resp.json()
    assert lesson_data["lesson_id"] == str(current_lesson_id)
    assert len(lesson_data["theory_sections"]) >= 1
    assert len(lesson_data["vocabulary"]) >= 1
    assert len(lesson_data["exercises"]) >= 1
    assert "correct_answer" in lesson_data["exercises"][0]

    # 6. Verify 404 on non-existent lesson
    fake_id = "00000000-0000-0000-0000-000000000000"
    not_found_resp = await client.get(f"/api/v1/lessons/{fake_id}", headers=headers)
    assert not_found_resp.status_code == 404

    # 7. Verify 403 Forbidden when an unauthorized user accesses an uncompleted/locked lesson
    unique_email = f"test_other_{uuid.uuid4().hex[:8]}@test.latium.ai"
    other_user = User(
        id=uuid.uuid4(),
        email=unique_email,
        hashed_password=test_user.hashed_password,
        full_name="Marcus Tullius",
        is_active=True,
    )
    db_session.add(other_user)
    await db_session.commit()

    other_token = create_access_token(subject=str(other_user.id))
    other_headers = {"Authorization": f"Bearer {other_token}"}

    # other_user has no completion and no progress on current_lesson_id
    forbidden_resp = await client.get(
        f"/api/v1/lessons/{current_lesson_id}", headers=other_headers
    )
    assert forbidden_resp.status_code == 403
    assert "Acesso negado" in forbidden_resp.json()["detail"]




import pytest
from httpx import AsyncClient

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

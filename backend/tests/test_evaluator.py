import uuid

import pytest
from httpx import AsyncClient

from app.agent.evaluator import evaluate_student_exercise
from app.agent.llm_factory import ModelRole, get_llm_for_role
from app.models.user import User
from app.schemas.evaluation import (
    ExerciseEvaluationRequest,
    ExerciseEvaluationResponse,
)


def test_llm_factory_fallback_resolution() -> None:
    """Verify that get_llm_for_role handles missing keys gracefully by falling back or returning None for mock."""
    router_llm = get_llm_for_role(ModelRole.ROUTER)
    tutor_llm = get_llm_for_role(ModelRole.TUTOR)
    evaluator_llm = get_llm_for_role(ModelRole.EVALUATOR)

    # In local test environment without API keys, factory returns None (mock fallback) or configured provider
    assert router_llm is None or hasattr(router_llm, "ainvoke")
    assert tutor_llm is None or hasattr(tutor_llm, "ainvoke")
    assert evaluator_llm is None or hasattr(evaluator_llm, "ainvoke")


@pytest.mark.asyncio
async def test_evaluator_exact_match_offline() -> None:
    """Verify that exact match Latin translation produces a 100 score and morphological breakdown."""
    req = ExerciseEvaluationRequest(
        lesson_id=str(uuid.uuid4()),
        exercise_id=1,
        question="A Itália é uma península.",
        expected_answer="Italia paeninsula est.",
        student_answer="Italia paeninsula est.",
        exercise_type="translation",
    )
    res: ExerciseEvaluationResponse = await evaluate_student_exercise(req)

    assert res.is_correct is True
    assert res.score == 100
    assert len(res.morphological_breakdown) >= 3
    # Check that tokens are extracted
    tokens = [m.token.lower() for m in res.morphological_breakdown]
    assert "italia" in tokens
    assert "est" in tokens


@pytest.mark.asyncio
async def test_evaluator_partial_match_offline() -> None:
    """Verify that close Latin translation receives a passing grade with feedback."""
    req = ExerciseEvaluationRequest(
        lesson_id=str(uuid.uuid4()),
        exercise_id=2,
        question="Sicília e Creta são ilhas.",
        expected_answer="Sicilia et Creta insulae sunt.",
        student_answer="Sicilia et Creta sunt insulae magnae.",
        exercise_type="translation",
    )
    res: ExerciseEvaluationResponse = await evaluate_student_exercise(req)

    assert res.is_correct is True
    assert res.score >= 70
    assert "censor" in res.evaluator_model.lower()


@pytest.mark.asyncio
async def test_evaluator_api_endpoint(
    client: AsyncClient,
    test_user: User,
) -> None:
    """Verify the POST /api/v1/lessons/{lesson_id}/evaluate FastAPI endpoint."""
    from app.core.security import create_access_token

    token = create_access_token(subject=str(test_user.id))
    auth_headers = {"Authorization": f"Bearer {token}"}

    # 1. Fetch available modules and pick a lesson
    mods_resp = await client.get("/api/v1/lessons/modules", headers=auth_headers)
    assert mods_resp.status_code == 200
    modules = mods_resp.json()
    assert len(modules) > 0
    lesson = modules[0]["lessons"][0]
    lesson_id = lesson["id"]

    # 2. Submit evaluation request
    payload = {
        "lesson_id": lesson_id,
        "exercise_id": 3,
        "question": "Roma está na Itália.",
        "expected_answer": "Roma in Italia est.",
        "student_answer": "Roma in Italia est.",
        "exercise_type": "translation",
    }
    eval_resp = await client.post(
        f"/api/v1/lessons/{lesson_id}/evaluate",
        json=payload,
        headers=auth_headers,
    )
    assert eval_resp.status_code == 200
    data = eval_resp.json()
    assert data["is_correct"] is True
    assert data["score"] == 100
    assert "morphological_breakdown" in data
    assert len(data["morphological_breakdown"]) > 0


@pytest.mark.asyncio
async def test_evaluator_invalid_lesson_404(
    client: AsyncClient,
    test_user: User,
) -> None:
    """Verify 404 response when evaluating against non-existent lesson."""
    from app.core.security import create_access_token

    token = create_access_token(subject=str(test_user.id))
    auth_headers = {"Authorization": f"Bearer {token}"}

    fake_id = str(uuid.uuid4())
    payload = {
        "lesson_id": fake_id,
        "exercise_id": 1,
        "question": "Teste",
        "expected_answer": "Teste",
        "student_answer": "Teste",
        "exercise_type": "translation",
    }
    resp = await client.post(
        f"/api/v1/lessons/{fake_id}/evaluate",
        json=payload,
        headers=auth_headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_evaluator_strict_orthography_and_rigor() -> None:
    """Verify that Censor Latium enforces orthographic rigor and penalizes accent defects."""
    # Test 1: Exact Latin translation receives perfect score
    req_exact = ExerciseEvaluationRequest(
        lesson_id=str(uuid.uuid4()),
        exercise_id=1,
        question="A Itália é uma península.",
        expected_answer="Italia paeninsula est.",
        student_answer="Italia paeninsula est.",
        exercise_type="translation",
    )
    res_exact: ExerciseEvaluationResponse = await evaluate_student_exercise(req_exact)
    assert res_exact.is_correct is True
    assert res_exact.score == 100

    # Test 2: Translation with correct Portuguese accents
    req_accent_correct = ExerciseEvaluationRequest(
        lesson_id=str(uuid.uuid4()),
        exercise_id=2,
        question="Traduza para o português: Mater filiam amat.",
        expected_answer="A mãe ama a filha.",
        student_answer="A mãe ama a filha.",
        exercise_type="translation",
    )
    res_correct: ExerciseEvaluationResponse = await evaluate_student_exercise(req_accent_correct)
    assert res_correct.is_correct is True
    assert res_correct.score == 100

    # Test 3: Translation omitting required accents is penalized by the Censor (score < 100)
    req_accent_missing = ExerciseEvaluationRequest(
        lesson_id=str(uuid.uuid4()),
        exercise_id=3,
        question="Traduza para o português: Mater filiam amat.",
        expected_answer="A mãe ama a filha.",
        student_answer="a mae ama a filha",
        exercise_type="translation",
    )
    res_missing: ExerciseEvaluationResponse = await evaluate_student_exercise(req_accent_missing)
    # The strict Censor detects the imperfection and penalizes score < 100
    assert res_missing.score < 100


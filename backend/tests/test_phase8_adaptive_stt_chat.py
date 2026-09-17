import io

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.tools import search_classical_web
from app.core.security import create_access_token
from app.models.user import User
from app.services.proficiency import (
    format_proficiency_for_prompt,
    get_student_proficiency_profile,
    record_exercise_result,
)
from app.services.stt import evaluate_pronunciation_phonetics


@pytest.mark.asyncio
async def test_adaptive_proficiency_lifecycle(
    db_session: AsyncSession,
    test_user: User,
) -> None:
    """Verify adaptive proficiency tracking updates mastery via EMA and identifies strengths and weaknesses."""
    user_id = test_user.id

    # 1. Baseline initialization
    initial_profile = await get_student_proficiency_profile(db_session, user_id)
    assert initial_profile.total_topics_tracked > 0
    assert initial_profile.overall_mastery == 0.0

    # 2. Record success in 1st_declension_nominative (score 100)
    await record_exercise_result(
        db=db_session,
        user_id=user_id,
        topic_keys=["1st_declension_nominative"],
        score=100,
    )
    # Record another success to raise mastery above 0.80
    for _ in range(4):
        await record_exercise_result(
            db=db_session,
            user_id=user_id,
            topic_keys=["1st_declension_nominative"],
            score=100,
        )

    # 3. Record failure in 1st_declension_accusative (score 40)
    await record_exercise_result(
        db=db_session,
        user_id=user_id,
        topic_keys=["1st_declension_accusative"],
        score=40,
        detected_errors=["confused_nominative_and_accusative"],
    )

    # 4. Check updated profile
    updated_profile = await get_student_proficiency_profile(db_session, user_id)
    assert "1st_declension_nominative" in updated_profile.mastered_topics
    assert "1st_declension_accusative" in updated_profile.vulnerable_topics

    # 5. Check formatted directives for prompt
    prompt_text = format_proficiency_for_prompt(updated_profile)
    assert "PERFIL ADAPTATIVO DO ALUNO" in prompt_text
    assert "1st_declension_nominative" in prompt_text
    assert "1st_declension_accusative" in prompt_text
    assert "DIRETRIZ PEDAGÓGICA ADAPTATIVA" in prompt_text


def test_phonetic_evaluator_pronuntiatio_restituta() -> None:
    """Verify classical phonetic evaluation respects Pronuntiatio Restituta rules."""
    target = "Veni vidi vici"
    transcribed = "veni vidi vici"

    result = evaluate_pronunciation_phonetics(
        target_text=target,
        transcribed_text=transcribed,
    )

    assert result.overall_score >= 90
    assert result.is_passing is True
    assert len(result.word_breakdown) == 3
    assert all(w.status == "correct" for w in result.word_breakdown)
    assert result.critical_phonemes_detected["restored_v_as_w"] is True
    assert result.critical_phonemes_detected["velar_c"] is True


def test_phonetic_evaluator_with_errors() -> None:
    """Verify phonetic evaluator flags pronunciation deviations and gives constructive tips."""
    target = "Roma in Italia est"
    transcribed = "Graecia et Hispania sunt"

    result = evaluate_pronunciation_phonetics(
        target_text=target,
        transcribed_text=transcribed,
    )

    assert result.overall_score < 70
    assert result.is_passing is False
    assert any(w.status == "needs_practice" for w in result.word_breakdown)
    assert "Persevere" in result.phonetic_tips


@pytest.mark.asyncio
async def test_stt_evaluation_api_endpoint(
    client: AsyncClient,
    test_user: User,
) -> None:
    """Verify POST /api/v1/media/stt/evaluate endpoint accepts multipart audio and returns phonetic breakdown."""
    token = create_access_token(subject=str(test_user.id))
    auth_headers = {"Authorization": f"Bearer {token}"}

    # Create dummy WAV bytes (riff header + silence)
    fake_wav_bytes = b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"

    files = {
        "audio_file": ("test_speech.wav", io.BytesIO(fake_wav_bytes), "audio/wav"),
    }
    data = {
        "target_text": "Puella pulchra cantat",
    }

    response = await client.post(
        "/api/v1/media/stt/evaluate",
        headers=auth_headers,
        files=files,
        data=data,
    )

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["target_text"] == "Puella pulchra cantat"
    assert "overall_score" in res_data
    assert "word_breakdown" in res_data
    assert len(res_data["word_breakdown"]) == 3
    assert "phonetic_tips" in res_data


@pytest.mark.asyncio
async def test_user_proficiency_api_endpoint(
    client: AsyncClient,
    test_user: User,
) -> None:
    """Verify GET /api/v1/users/me/proficiency returns structured proficiency data."""
    token = create_access_token(subject=str(test_user.id))
    auth_headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/users/me/proficiency", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == str(test_user.id)
    assert "overall_mastery" in data
    assert "topic_details" in data
    assert len(data["topic_details"]) > 0


@pytest.mark.asyncio
async def test_search_classical_web_tool() -> None:
    """Verify search_classical_web tool returns historical facts and archaeological references."""
    pompeii_fact = await search_classical_web.ainvoke({"query": "Pompeia pão escravo"})
    assert "Pompeia" in pompeii_fact
    assert "padarias" in pompeii_fact or "Celeris" in pompeii_fact

    gladius_fact = await search_classical_web.ainvoke({"query": "gladius legiões"})
    assert "Gladius" in gladius_fact
    assert "scutum" in gladius_fact or "espada" in gladius_fact


@pytest.mark.asyncio
async def test_chat_interactive_endpoint(
    client: AsyncClient,
    test_user: User,
) -> None:
    """Verify POST /api/v1/chat/interactive provides dialogue with Magister enriched with web knowledge."""
    token = create_access_token(subject=str(test_user.id))
    auth_headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "message": "Magister, como era o pão em Pompeia?",
        "context_topics": ["1st_declension_nominative"],
    }

    response = await client.post(
        "/api/v1/chat/interactive", headers=auth_headers, json=payload
    )
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert len(data["reply"]) > 20
    assert "sources_consulted" in data
    assert any(
        "Web" in s or "Alexandria" in s or "Tradição" in s
        for s in data["sources_consulted"]
    )


def test_phonetic_evaluation_accuracy() -> None:
    """Verify phonetic evaluation produces realistic scores and avoids fake 100% scores."""
    from app.services.stt import evaluate_pronunciation_phonetics

    # 1. Perfect match
    perfect = evaluate_pronunciation_phonetics(
        target_text="Puella pulchra cantat",
        transcribed_text="Puella pulchra cantat",
    )
    assert perfect.overall_score == 100
    assert perfect.is_passing is True
    assert all(w.status == "correct" for w in perfect.word_breakdown)

    # 2. Complete mismatch (Portuguese words)
    mismatch = evaluate_pronunciation_phonetics(
        target_text="Puella pulchra cantat",
        transcribed_text="Menina bonita canta",
    )
    assert mismatch.overall_score < 50
    assert mismatch.is_passing is False
    assert any(w.status == "needs_practice" for w in mismatch.word_breakdown)

    # 3. Empty / silence audio
    silence = evaluate_pronunciation_phonetics(
        target_text="Puella pulchra cantat",
        transcribed_text="",
    )
    assert silence.overall_score == 0
    assert silence.is_passing is False
    assert all(w.status == "needs_practice" for w in silence.word_breakdown)


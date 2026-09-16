import pytest
from httpx import AsyncClient

from app.agent.illustrator import (
    _generate_classical_roman_svg,
    create_flashcard_for_word,
)
from app.models.user import User


def test_generate_classical_roman_svg_properties() -> None:
    """Verify SVG generation contains Latin word, gold palette and valid SVG markup."""
    svg = _generate_classical_roman_svg(
        word="gladius",
        translation="espada curta",
        grammatical_class="Substantivo masculino",
    )
    assert "<svg" in svg
    assert "</svg>" in svg
    assert "GLADIUS" in svg
    assert "espada curta" in svg
    assert "SENATUS POPULUSQUE ROMANUS" in svg
    assert "#d4af37" in svg or "goldGrad" in svg


@pytest.mark.asyncio
async def test_create_flashcard_for_word() -> None:
    """Verify create_flashcard_for_word produces a complete multimodal card."""
    card = await create_flashcard_for_word(
        word="puella",
        dictionary_entry="puella, -ae, f.",
        grammatical_class="Substantivo feminino de 1ª declinação",
        translation="menina, donzela",
        example_sentence="Puella cantat.",
    )
    assert card.word == "puella"
    assert card.image_url is not None and card.image_url.endswith(".svg")
    assert card.audio_url is not None and "/api/v1/media/audio/" in card.audio_url
    assert card.audio_base64 is not None and len(card.audio_base64) > 0


@pytest.mark.asyncio
async def test_lesson_flashcards_api_endpoint(
    client: AsyncClient,
    test_user: User,
) -> None:
    """Verify GET /api/v1/flashcards/lesson/{lesson_id} endpoint."""
    from app.core.security import create_access_token

    token = create_access_token(subject=str(test_user.id))
    auth_headers = {"Authorization": f"Bearer {token}"}

    # 1. Fetch available modules to get a valid lesson_id
    mods_resp = await client.get("/api/v1/lessons/modules", headers=auth_headers)
    assert mods_resp.status_code == 200
    modules = mods_resp.json()
    assert len(modules) > 0
    lesson_id = modules[0]["lessons"][0]["id"]

    # 2. Get flashcards for the lesson
    fc_resp = await client.get(
        f"/api/v1/flashcards/lesson/{lesson_id}", headers=auth_headers
    )
    assert fc_resp.status_code == 200
    data = fc_resp.json()

    assert data["lesson_id"] == lesson_id
    assert data["total_cards"] > 0
    assert len(data["flashcards"]) > 0

    first_card = data["flashcards"][0]
    assert "word" in first_card
    assert "translation" in first_card
    assert "image_url" in first_card
    assert "audio_url" in first_card

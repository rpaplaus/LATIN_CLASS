import io
import wave

import pytest
from httpx import AsyncClient

from app.models.user import User
from app.services.tts import (
    _generate_synthetic_fallback_audio,
    generate_audio_hash,
    get_or_create_latin_tts,
)


def test_generate_audio_hash_deterministic() -> None:
    """Verify audio hash is identical for identical words and changes across voices or text."""
    h1 = generate_audio_hash("Gallia est omnis divisa", "onyx")
    h2 = generate_audio_hash("  gallia est omnis divisa  ", "ONYX")
    h3 = generate_audio_hash("Gallia est omnis divisa", "alloy")
    h4 = generate_audio_hash("Roma caput mundi est", "onyx")

    assert h1 == h2
    assert h1 != h3
    assert h1 != h4
    assert len(h1) == 64


def test_synthetic_fallback_audio_valid_wav() -> None:
    """Verify synthetic fallback generates a valid, decodable PCM WAV buffer."""
    audio_bytes = _generate_synthetic_fallback_audio("puella cantat")
    assert len(audio_bytes) > 1000

    # Ensure python wave module can open and read header correctly
    buf = io.BytesIO(audio_bytes)
    with wave.open(buf, "rb") as w:
        assert w.getnchannels() == 1
        assert w.getsampwidth() == 2
        assert w.getframerate() == 22050
        assert w.getnframes() > 0


@pytest.mark.asyncio
async def test_get_or_create_latin_tts_dual_cache() -> None:
    """Verify get_or_create_latin_tts generates audio and returns cached on second call."""
    text = "Senatus Populusque Romanus"
    # First invocation: generates and writes to disk
    b1, h1, b64_1, cached1 = await get_or_create_latin_tts(text, voice="onyx")
    assert len(b1) > 0
    assert len(b64_1) > 0
    assert cached1 is False

    # Second invocation: should hit disk cache
    b2, h2, b64_2, _cached2 = await get_or_create_latin_tts(text, voice="onyx")
    assert h1 == h2
    assert b1 == b2
    assert b64_1 == b64_2


@pytest.mark.asyncio
async def test_media_tts_api_and_streaming(
    client: AsyncClient,
    test_user: User,
) -> None:
    """Verify POST /api/v1/media/tts and GET /api/v1/media/audio/{hash} endpoints."""
    from app.core.security import create_access_token

    token = create_access_token(subject=str(test_user.id))
    auth_headers = {"Authorization": f"Bearer {token}"}

    # 1. Request TTS generation
    tts_payload = {"text": "Alea iacta est", "voice": "onyx"}
    resp = await client.post(
        "/api/v1/media/tts", json=tts_payload, headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()

    assert "audio_hash" in data
    assert "audio_url" in data
    assert "audio_base64" in data
    assert data["text"] == "Alea iacta est"

    audio_hash = data["audio_hash"]

    # 2. Stream audio file directly
    stream_resp = await client.get(f"/api/v1/media/audio/{audio_hash}")
    assert stream_resp.status_code == 200
    assert stream_resp.headers["content-type"] == "audio/mpeg"
    assert "public, max-age=" in stream_resp.headers["cache-control"]
    assert len(stream_resp.content) > 0


@pytest.mark.asyncio
async def test_media_audio_not_found(client: AsyncClient) -> None:
    """Verify 404 response for non-existent audio hash."""
    resp = await client.get(
        "/api/v1/media/audio/0000000000000000000000000000000000000000000000000000000000000000"
    )
    assert resp.status_code == 404

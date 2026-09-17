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
    import uuid
    text = f"Senatus Populusque Romanus {uuid.uuid4().hex[:8]}"
    # First invocation: generates and writes to disk
    b1, h1, b64_1, cached1 = await get_or_create_latin_tts(text, voice="onyx")
    assert len(b1) > 0
    assert len(b64_1) > 0
    assert cached1 is False

    # Second invocation: should hit disk cache
    b2, h2, b64_2, cached2 = await get_or_create_latin_tts(text, voice="onyx")
    assert h1 == h2
    assert b1 == b2
    assert b64_1 == b64_2
    assert cached2 is True


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


@pytest.mark.asyncio
async def test_call_openai_tts_padding_and_validation() -> None:
    """Verify _call_openai_tts_with_retry applies terminal punctuation padding and validates >= 1KB."""
    from unittest.mock import AsyncMock, patch
    from app.services.tts import _call_openai_tts_with_retry

    mock_client = AsyncMock()
    mock_speech = AsyncMock()
    mock_client.audio.speech = mock_speech

    # 1. Test padding is applied
    mock_response = AsyncMock()
    mock_response.content = b"x" * 2048
    mock_speech.create.return_value = mock_response

    with patch("openai.AsyncOpenAI", return_value=mock_client), \
         patch("app.core.config.settings.OPENAI_API_KEY", "mock-key"):
        result = await _call_openai_tts_with_retry("esse", voice="onyx")
        assert len(result) == 2048
        # Verify prompt passed to OpenAI ended with a period
        _, kwargs = mock_speech.create.call_args
        assert kwargs["input"] == "esse."

    # 2. Test text that already has punctuation is preserved
    with patch("openai.AsyncOpenAI", return_value=mock_client), \
         patch("app.core.config.settings.OPENAI_API_KEY", "mock-key"):
        await _call_openai_tts_with_retry("quid agis?", voice="onyx")
        _, kwargs = mock_speech.create.call_args
        assert kwargs["input"] == "quid agis?"

    # 3. Test that truncated / small response (< 1024 bytes) raises ValueError
    bad_response = AsyncMock()
    bad_response.content = b"x" * 500  # < 1KB
    mock_speech.create.return_value = bad_response

    with patch("openai.AsyncOpenAI", return_value=mock_client), \
         patch("app.core.config.settings.OPENAI_API_KEY", "mock-key"):
        with pytest.raises(Exception) as exc_info:
            await _call_openai_tts_with_retry("ne", voice="onyx", max_retries=1)
        assert "< 1KB" in str(exc_info.value) or "inferior a 1KB" in str(exc_info.value)


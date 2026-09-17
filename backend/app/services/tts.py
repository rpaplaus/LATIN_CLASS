import base64
import hashlib
import io
import logging
import math
import struct
import wave
from pathlib import Path
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

# Base storage directory for cached audio files
STORAGE_DIR = Path(__file__).resolve().parent.parent.parent / "storage" / "audio"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

REDIS_TTL_SECONDS = 2592000  # 30 days


def generate_audio_hash(text: str, voice: str) -> str:
    """Generate deterministic SHA-256 hash for normalized text and voice parameters."""
    normalized = f"{text.strip().lower()}:{voice.strip().lower()}"
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _generate_synthetic_fallback_audio(text: str) -> bytes:
    """Generate a clean synthetic PCM WAV audio buffer when OpenAI TTS is not configured or fails.

    Produces a valid, audible 0.3s pleasant acoustic chime so that tests and offline browsers
    can play back the pronunciation without error.
    """
    buf = io.BytesIO()
    sample_rate = 22050
    duration_sec = 0.3
    num_samples = int(sample_rate * duration_sec)

    # Vary pitch slightly based on string hash for character
    h_val = sum(text.encode("utf-8")) % 50
    freq = 440.0 + h_val

    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)

        samples = []
        for i in range(num_samples):
            # Smooth attack and decay envelope
            envelope = math.sin(math.pi * i / num_samples)
            sine = math.sin(2.0 * math.pi * freq * i / sample_rate)
            val = int(sine * envelope * 12000)
            samples.append(struct.pack("<h", val))

        w.writeframes(b"".join(samples))

    return buf.getvalue()


async def _call_openai_tts_with_retry(
    clean_text: str, voice: str, max_retries: int = 2
) -> bytes:
    """Call OpenAI TTS API with timeout and retry logic."""
    import asyncio

    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY, timeout=8.0)
    last_exc: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            logger.debug(
                "Calling OpenAI TTS (attempt %d/%d) for text: '%s'",
                attempt,
                max_retries,
                clean_text,
            )
            response = await client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=clean_text,
            )
            if response.content and len(response.content) > 100:
                return response.content
            raise ValueError("Resposta de áudio vazia ou truncada da OpenAI")
        except Exception as exc:
            last_exc = exc
            logger.warning(
                "OpenAI TTS attempt %d/%d failed for '%s': %s",
                attempt,
                max_retries,
                clean_text,
                exc,
            )
            if attempt < max_retries:
                await asyncio.sleep(0.5 * attempt)
    raise last_exc or RuntimeError("OpenAI TTS falhou em todas as tentativas")


async def get_or_create_latin_tts(
    text: str,
    voice: str = "onyx",
    redis_client: Any | None = None,
) -> tuple[bytes, str, str, bool]:
    """Retrieve or generate audio pronunciation for Latin text using dual Redis/disk caching.

    Returns:
        (audio_bytes, audio_hash, audio_base64, was_cached)
    """
    clean_text = text.strip()
    if not clean_text:
        raise ValueError("Texto para síntese de pronúncia não pode ser vazio.")

    audio_hash = generate_audio_hash(clean_text, voice)
    redis_key = f"latin_tts:audio:{audio_hash}"
    file_path = STORAGE_DIR / f"{audio_hash}.mp3"
    import anyio.to_thread

    # 1. Check Redis Cache (Level 1)
    if redis_client:
        try:
            cached_b64 = await redis_client.get(redis_key)
            if cached_b64:
                audio_bytes = base64.b64decode(cached_b64)
                if audio_bytes.startswith(b"RIFF") and settings.OPENAI_API_KEY:
                    logger.info(
                        "Found synthetic WAV in Redis for %s; reheating with genuine TTS.",
                        audio_hash,
                    )
                else:
                    logger.debug("TTS Cache HIT in Redis for hash %s", audio_hash)
                    return audio_bytes, audio_hash, cached_b64, True
        except Exception as exc:
            logger.warning("Failed to read TTS from Redis cache: %s", exc)

    # 2. Check Local Disk Cache (Level 2)
    if file_path.exists():
        try:
            audio_bytes = await anyio.to_thread.run_sync(file_path.read_bytes)
            if audio_bytes.startswith(b"RIFF") and settings.OPENAI_API_KEY:
                logger.info(
                    "Found synthetic WAV on disk for %s; reheating with genuine TTS.",
                    audio_hash,
                )
            else:
                audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
                logger.debug(
                    "TTS Cache HIT on Disk for hash %s. Reheating Redis.", audio_hash
                )

                if redis_client:
                    try:
                        await redis_client.set(
                            redis_key, audio_b64, ex=REDIS_TTL_SECONDS
                        )
                    except Exception as exc:
                        logger.warning("Failed to reheat Redis TTS cache: %s", exc)

                return audio_bytes, audio_hash, audio_b64, True
        except Exception as exc:
            logger.warning("Failed to read audio from disk (%s): %s", file_path, exc)

    # 3. Generate Audio (Level 3 - Provider or Fallback)
    generated_bytes: bytes
    is_synthetic = False
    if settings.OPENAI_API_KEY:
        try:
            generated_bytes = await _call_openai_tts_with_retry(clean_text, voice)
            logger.info(
                "Generated OpenAI TTS audio for '%s' (%s)", clean_text, audio_hash
            )
        except Exception as exc:
            logger.warning(
                "OpenAI TTS API failed after retries (%s). Falling back to synthetic audio.",
                exc,
            )
            generated_bytes = await anyio.to_thread.run_sync(
                _generate_synthetic_fallback_audio, clean_text
            )
            is_synthetic = True
    else:
        logger.info("No OpenAI API key. Using deterministic synthetic Latin audio.")
        generated_bytes = await anyio.to_thread.run_sync(
            _generate_synthetic_fallback_audio, clean_text
        )
        is_synthetic = True

    # 4. Save to Disk Cache & Redis Cache (Persist both genuine and synthetic to guarantee valid URLs)
    audio_b64 = base64.b64encode(generated_bytes).decode("ascii")
    try:
        await anyio.to_thread.run_sync(file_path.write_bytes, generated_bytes)
    except Exception as exc:
        logger.warning("Failed to save audio to disk (%s): %s", file_path, exc)

    if redis_client:
        try:
            # Synthetic audio is cached with a shorter TTL (1 hour) to allow eventual reheating
            ttl = 3600 if is_synthetic else REDIS_TTL_SECONDS
            await redis_client.set(redis_key, audio_b64, ex=ttl)
        except Exception as exc:
            logger.warning("Failed to save TTS to Redis cache: %s", exc)

    return generated_bytes, audio_hash, audio_b64, False

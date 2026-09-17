import base64
import logging
from typing import Any

import redis.asyncio as aioredis
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse

from app.core.redis import get_redis
from app.schemas.media import (
    PronunciationEvaluationResponse,
    TTSRequest,
    TTSResponse,
)
from app.services.stt import evaluate_latin_pronunciation
from app.services.tts import (
    STORAGE_DIR,
    get_or_create_latin_tts,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/tts", response_model=TTSResponse)
async def generate_latin_tts(
    req: TTSRequest,
    redis: aioredis.Redis = Depends(get_redis),
) -> Any:
    """Generate or retrieve cached audio pronunciation for Latin text."""
    try:
        audio_bytes, audio_hash, audio_b64, was_cached = await get_or_create_latin_tts(
            text=req.text,
            voice=req.voice,
            redis_client=redis,
        )
        mime_type = "audio/wav" if audio_bytes.startswith(b"RIFF") else "audio/mpeg"
        return TTSResponse(
            audio_hash=audio_hash,
            audio_url=f"/api/v1/media/audio/{audio_hash}",
            audio_base64=audio_b64,
            cached=was_cached,
            text=req.text.strip(),
            voice=req.voice,
            mime_type=mime_type,
        )
    except Exception as exc:
        logger.error("Failed to generate Latin audio: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao sintetizar áudio latino: {exc}",
        ) from exc


@router.post("/stt/evaluate", response_model=PronunciationEvaluationResponse)
async def evaluate_speech_pronunciation(
    audio_file: UploadFile = File(...),
    target_text: str = Form(...),
) -> Any:
    """Evaluate student spoken Latin audio against target classical phrase."""
    try:
        audio_bytes = await audio_file.read()
        if len(audio_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Arquivo de áudio vazio. Grave sua pronúncia novamente.",
            )

        filename = audio_file.filename or "recording.wav"
        result = await evaluate_latin_pronunciation(
            audio_bytes=audio_bytes,
            target_text=target_text,
            filename=filename,
        )
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to evaluate Latin speech pronunciation: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao avaliar pronúncia clássica: {exc}",
        ) from exc


@router.get("/audio/{audio_hash}")
async def get_audio_file(
    audio_hash: str,
    redis: aioredis.Redis = Depends(get_redis),
) -> Response:
    """Stream cached Latin audio file directly to browser with immutable cache headers."""
    # 1. Try Redis
    try:
        cached_b64 = await redis.get(f"latin_tts:audio:{audio_hash}")
        if cached_b64:
            audio_bytes = base64.b64decode(cached_b64)
            media_type = "audio/wav" if audio_bytes.startswith(b"RIFF") else "audio/mpeg"
            return Response(
                content=audio_bytes,
                media_type=media_type,
                headers={
                    "Cache-Control": "public, max-age=2592000, immutable",
                    "Accept-Ranges": "bytes",
                },
            )
    except Exception as exc:
        logger.warning("Redis lookup failed in /audio: %s", exc)

    # 2. Try Disk (Non-blocking async streaming via FileResponse)
    file_path = STORAGE_DIR / f"{audio_hash}.mp3"
    if file_path.exists():
        import anyio.to_thread

        try:
            header = await anyio.to_thread.run_sync(
                lambda: file_path.read_bytes()[:4]
            )
            media_type = "audio/wav" if header.startswith(b"RIFF") else "audio/mpeg"
        except Exception:
            media_type = "audio/mpeg"

        return FileResponse(
            path=file_path,
            media_type=media_type,
            headers={
                "Cache-Control": "public, max-age=2592000, immutable",
                "Accept-Ranges": "bytes",
            },
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Arquivo de áudio não encontrado na Biblioteca de Alexandria.",
    )


@router.get("/images/{filename}")
async def get_image_file(filename: str) -> Response:
    """Serve cached Roman classical artwork and flashcard illustration images via async FileResponse."""
    from app.agent.illustrator import IMAGES_STORAGE_DIR

    file_path = IMAGES_STORAGE_DIR / filename
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ilustração romana não encontrada na galeria do Senado.",
        )

    content_type = "image/svg+xml" if filename.endswith(".svg") else "image/webp"
    headers = {
        "Cache-Control": "public, max-age=2592000, immutable",
        "X-Content-Type-Options": "nosniff",
    }
    if content_type == "image/svg+xml":
        headers["Content-Security-Policy"] = (
            "default-src 'none'; style-src 'unsafe-inline'"
        )

    return FileResponse(
        path=file_path,
        media_type=content_type,
        headers=headers,
    )

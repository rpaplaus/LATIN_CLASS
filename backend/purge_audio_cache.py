"""Temporary Maintenance Script: TTS Audio Cache Purge & Database Cleanup.

Finds all audio files in backend/storage/audio/ with size < 2KB (plus silent legacy cache),
deletes them, evicts corresponding Redis cache keys, and cleans audio_url references
in lessons.content JSONB in PostgreSQL.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add backend directory to sys.path so app modules import cleanly
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified

from app.core.config import settings
from app.core.database import async_session_factory
from app.models.course import Lesson
from app.services.tts import (
    STORAGE_DIR,
    generate_audio_hash,
    get_or_create_latin_tts,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cache_purge")


async def run_cache_purge() -> None:
    logger.info("=== Starting TTS Cache Purge and Maintenance ===")
    logger.info("Target Storage Directory: %s", STORAGE_DIR)

    # Hashes to explicitly purge (e.g. known silent/corrupted files)
    voice = getattr(settings, "OPENAI_TTS_VOICE", "onyx")
    esse_hash = generate_audio_hash("esse", voice)
    ne_hash = generate_audio_hash("ne", voice)
    explicit_bad_hashes = {esse_hash, ne_hash}

    logger.info("Targeted known hashes: esse=%s, ne=%s", esse_hash, ne_hash)

    # 1. Scan and delete audio files < 2KB or matching known bad hashes
    purged_hashes: set[str] = set()
    deleted_files: list[str] = []

    if STORAGE_DIR.exists():
        for file in STORAGE_DIR.glob("*.mp3"):
            try:
                size = file.stat().st_size
                stem = file.stem  # Hash string without .mp3
                is_under_2kb = size < 2048
                is_explicit_bad = stem in explicit_bad_hashes

                if is_under_2kb or is_explicit_bad:
                    reason = f"<2KB ({size} bytes)" if is_under_2kb else "Explicit bad/silent audio"
                    logger.info("Deleting file: %s (%s)", file.name, reason)
                    file.unlink(missing_ok=True)
                    purged_hashes.add(stem)
                    deleted_files.append(file.name)
            except Exception as exc:
                logger.error("Error inspecting/deleting %s: %s", file, exc)

    logger.info(
        "Phase 1 complete: %d files deleted from disk storage.", len(deleted_files)
    )

    # 2. Purge matching Redis keys
    redis_evicted = 0
    try:
        redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=False)
        # Check all purged hashes + known hashes
        all_hashes_to_evict = purged_hashes.union(explicit_bad_hashes)
        for h in all_hashes_to_evict:
            redis_key = f"latin_tts:audio:{h}"
            res = await redis_client.delete(redis_key)
            if res > 0:
                redis_evicted += res
                logger.info("Evicted Redis key: %s", redis_key)
        await redis_client.close()
    except Exception as exc:
        logger.warning("Could not clear Redis cache keys: %s", exc)

    logger.info("Phase 2 complete: %d Redis keys evicted.", redis_evicted)

    # 3. Clean audio_url in lessons.content JSONB
    updated_lessons_count = 0
    cleaned_items_count = 0

    async with async_session_factory() as session:
        result = await session.execute(select(Lesson))
        lessons = result.scalars().all()

        for lesson in lessons:
            if not lesson.content or not isinstance(lesson.content, dict):
                continue

            content_modified = False
            vocabulary = lesson.content.get("vocabulary", [])

            if isinstance(vocabulary, list):
                for item in vocabulary:
                    if isinstance(item, dict):
                        word = item.get("word", "").strip().lower()
                        audio_url = item.get("audio_url")
                        # Check if audio_url points to a purged hash or if word is esse/ne
                        item_hash = generate_audio_hash(word, voice) if word else ""

                        should_clear = False
                        if audio_url:
                            for ph in all_hashes_to_evict:
                                if ph in str(audio_url):
                                    should_clear = True
                                    break
                            if word in ["esse", "ne"]:
                                should_clear = True

                        if should_clear:
                            logger.info(
                                "Clearing audio_url in lesson '%s' (ID: %s) for word '%s' (was: %s)",
                                lesson.title,
                                lesson.id,
                                word,
                                audio_url,
                            )
                            item["audio_url"] = None
                            content_modified = True
                            cleaned_items_count += 1

            if content_modified:
                flag_modified(lesson, "content")
                session.add(lesson)
                updated_lessons_count += 1

        if updated_lessons_count > 0:
            await session.commit()
            logger.info(
                "Phase 3 complete: %d lessons updated, %d vocabulary items cleaned.",
                updated_lessons_count,
                cleaned_items_count,
            )
        else:
            logger.info(
                "Phase 3 complete: No lessons had stale audio_url in content JSONB."
            )

    # 4. Verification: Re-generate high-quality audio for 'esse' and 'ne' with padding & size check
    logger.info("Phase 4: Re-generating fresh TTS audio for 'esse' and 'ne' with punctuation padding...")
    redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=False)
    for test_word in ["esse", "ne"]:
        try:
            audio_bytes, a_hash, a_b64, was_cached = await get_or_create_latin_tts(
                text=test_word,
                voice=voice,
                redis_client=redis_client,
            )
            logger.info(
                "Successfully generated TTS for '%s': hash=%s, size=%d bytes, was_cached=%s",
                test_word,
                a_hash,
                len(audio_bytes),
                was_cached,
            )
            assert len(audio_bytes) >= 1024, f"Audio for {test_word} is under 1KB!"
            file_on_disk = STORAGE_DIR / f"{a_hash}.mp3"
            assert file_on_disk.exists(), f"File {file_on_disk} was not written to disk!"
            assert file_on_disk.stat().st_size >= 1024, f"File on disk is under 1KB!"
        except Exception as exc:
            logger.error("Failed to generate test TTS for '%s': %s", test_word, exc)
            raise
    await redis_client.close()

    logger.info("=== Hotfix Maintenance Completed Successfully! ===")


if __name__ == "__main__":
    asyncio.run(run_cache_purge())

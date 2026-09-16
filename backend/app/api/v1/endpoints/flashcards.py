import logging
import uuid

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.illustrator import create_flashcard_for_word
from app.api.deps import get_current_user, get_db
from app.core.redis import get_redis
from app.models.course import Lesson
from app.models.user import User
from app.schemas.flashcard import FlashcardItem, LessonFlashcardsResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# Canonical vocabulary sets mapped by grammar topic keyword
TOPIC_VOCABULARY = {
    "1a_declinacao": [
        (
            "puella",
            "puella, -ae, f.",
            "Substantivo feminino de 1ª declinação",
            "menina, jovem donzela",
            "Puella pulchra in horto ambulat.",
        ),
        (
            "insula",
            "insula, -ae, f.",
            "Substantivo feminino de 1ª declinação",
            "ilha",
            "Corsica et Sardinia magnae insulae sunt.",
        ),
        (
            "terra",
            "terra, -ae, f.",
            "Substantivo feminino de 1ª declinação",
            "terra, solo, pátria",
            "Terra Italiae fertilis est.",
        ),
        (
            "gladius",
            "gladius, -i, m.",
            "Substantivo masculino de 2ª declinação",
            "espada curta romana",
            "Miles fortem gladium gerit.",
        ),
    ],
    "verbo_esse": [
        (
            "esse",
            "sum, es, esse, fui",
            "Verbo irregular de ligação",
            "ser, estar, existir",
            "Roma in Italia est.",
        ),
        (
            "habitare",
            "habito, -as, -are, -avi, -atum",
            "Verbo regular de 1ª conjugação",
            "habitar, morar",
            "Agricola in villa habitat.",
        ),
        (
            "amare",
            "amo, -as, -are, -avi, -atum",
            "Verbo regular de 1ª conjugação",
            "amar, estimar",
            "Discipulus linguam Latinam amat.",
        ),
    ],
    "default": [
        (
            "puella",
            "puella, -ae, f.",
            "Substantivo feminino de 1ª declinação",
            "menina, jovem",
            "Puella cantat.",
        ),
        (
            "roma",
            "Roma, -ae, f.",
            "Nome próprio feminino de 1ª declinação",
            "Roma",
            "Roma caput mundi est.",
        ),
        (
            "gladius",
            "gladius, -i, m.",
            "Substantivo masculino de 2ª declinação",
            "espada romana",
            "Miles gladium stringit.",
        ),
        (
            "magnus",
            "magnus, -a, -um",
            "Adjetivo de 1ª e 2ª classe",
            "grande, ilustre",
            "Magnum imperium Romanum est.",
        ),
    ],
}


@router.get("/lesson/{lesson_id}", response_model=LessonFlashcardsResponse)
async def get_lesson_flashcards(
    lesson_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    redis: aioredis.Redis = Depends(get_redis),
) -> LessonFlashcardsResponse:
    """Generate or retrieve multimodal visual and audio flashcards for a specific Latin lesson."""
    stmt = select(Lesson).where(Lesson.id == lesson_id)
    lesson = (await db.execute(stmt)).scalar_one_or_none()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lição não encontrada.",
        )

    # Determine relevant vocabulary based on lesson grammar topics
    vocab_tuples = TOPIC_VOCABULARY["default"]
    if lesson.grammar_topics:
        topics_str = str(lesson.grammar_topics).lower()
        if "declina" in topics_str or "nominativ" in topics_str:
            vocab_tuples = TOPIC_VOCABULARY["1a_declinacao"]
        elif "verbo" in topics_str or "esse" in topics_str:
            vocab_tuples = TOPIC_VOCABULARY["verbo_esse"]

    flashcards: list[FlashcardItem] = []
    for word, entry, g_class, trans, sentence in vocab_tuples:
        card = await create_flashcard_for_word(
            word=word,
            dictionary_entry=entry,
            grammatical_class=g_class,
            translation=trans,
            example_sentence=sentence,
            redis_client=redis,
        )
        flashcards.append(card)

    return LessonFlashcardsResponse(
        lesson_id=str(lesson.id),
        lesson_title=lesson.title,
        total_cards=len(flashcards),
        flashcards=flashcards,
    )

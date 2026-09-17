import json
import logging
import re
import uuid
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.llm_factory import ModelRole, get_llm_for_role
from app.api.deps import get_current_user, get_db
from app.models.progress import StudentTopicProficiency
from app.models.user import User
from app.schemas.arena import (
    ArenaChallengeResponse,
    ArenaEvaluationRequest,
    ArenaEvaluationResponse,
    ArenaFlashcard,
    ArenaGenerateRequest,
)
from app.services.proficiency import (
    CANONICAL_CURRICULUM_TOPICS,
    CANONICAL_TOPIC_PORTUGUESE,
    normalize_topic_key,
    record_exercise_result,
)
from app.services.tts import generate_audio_hash

logger = logging.getLogger(__name__)

router = APIRouter()

# Curated canonical mini-decks for deterministic fallback (0 tokens / offline / tests)
CANONICAL_MINI_DECKS: dict[str, list[dict[str, str]]] = {
    "1st_declension_accusative": [
        {
            "id": "1",
            "latin": "Puellam video.",
            "translation": "Eu vejo a menina.",
            "hint": "Desinência '-am' marca o objeto direto acusativo singular.",
        },
        {
            "id": "2",
            "latin": "Nauta insulam navigat.",
            "translation": "O marinheiro navega para a ilha.",
            "hint": "Insulam indica a direção ou o alvo da navegação.",
        },
        {
            "id": "3",
            "latin": "Agricola villam curat.",
            "translation": "O agricultor cuida da casa de campo.",
            "hint": "Villam é o objeto direto cuidado pelo lavrador.",
        },
    ],
    "1st_declension_nominative": [
        {
            "id": "1",
            "latin": "Puella cantat.",
            "translation": "A menina canta.",
            "hint": "Puella no nominativo singular feminino como sujeito.",
        },
        {
            "id": "2",
            "latin": "Roma in Italia est.",
            "translation": "Roma está na Itália.",
            "hint": "Roma é o sujeito da oração com o verbo esse.",
        },
        {
            "id": "3",
            "latin": "Insulae magnae sunt.",
            "translation": "As ilhas são grandes.",
            "hint": "Insulae e magnae concordam no nominativo plural.",
        },
    ],
    "verb_esse_present": [
        {
            "id": "1",
            "latin": "Marcus servus non est.",
            "translation": "Marco não é um escravo.",
            "hint": "Est é a 3ª pessoa do singular do verbo esse.",
        },
        {
            "id": "2",
            "latin": "Discipuli laeti sunt.",
            "translation": "Os alunos estão felizes.",
            "hint": "Sunt é a 3ª pessoa do plural.",
        },
        {
            "id": "3",
            "latin": "Ego sum Romanus.",
            "translation": "Eu sou romano.",
            "hint": "Sum é a 1ª pessoa do singular do presente.",
        },
    ],
    "2nd_declension_masculine": [
        {
            "id": "1",
            "latin": "Dominus servum vocat.",
            "translation": "O senhor chama o escravo.",
            "hint": "Dominus é o sujeito da 2ª declinação em -us.",
        },
        {
            "id": "2",
            "latin": "Amicus in horto ambulat.",
            "translation": "O amigo caminha no jardim.",
            "hint": "Amicus é substantivo masculino da 2ª declinação.",
        },
        {
            "id": "3",
            "latin": "Pueri libros legunt.",
            "translation": "Os meninos leem os livros.",
            "hint": "Pueri é nominativo plural em -i.",
        },
    ],
}


async def _select_target_topic(
    db: AsyncSession,
    user_id: uuid.UUID,
    requested_topic: str | None,
) -> tuple[str, str, float]:
    """Select the target grammar topic for the student's Arena combat.

    Prioritizes the lowest mastery score (EMA) with attempts_count > 0.
    """
    if requested_topic:
        normalized = normalize_topic_key(requested_topic)
        label = CANONICAL_TOPIC_PORTUGUESE.get(
            normalized, normalized.replace("_", " ").title()
        )
        query = select(StudentTopicProficiency).where(
            StudentTopicProficiency.user_id == user_id,
            StudentTopicProficiency.topic_key == normalized,
        )
        res = (await db.execute(query)).scalar_one_or_none()
        mastery = res.mastery_score if res else 0.50
        return normalized, label, mastery

    # Fetch all student topic records
    query = (
        select(StudentTopicProficiency)
        .where(StudentTopicProficiency.user_id == user_id)
        .order_by(StudentTopicProficiency.mastery_score.asc())
    )
    result = await db.execute(query)
    records = list(result.scalars().all())

    # Priority 1: Attempted topics with mastery < 0.60, lowest first
    vulnerable_attempted = [
        r for r in records if r.attempts_count > 0 and r.mastery_score < 0.60
    ]
    if vulnerable_attempted:
        target = min(vulnerable_attempted, key=lambda x: x.mastery_score)
        label = CANONICAL_TOPIC_PORTUGUESE.get(
            target.topic_key, target.topic_key.replace("_", " ").title()
        )
        return target.topic_key, label, target.mastery_score

    # Priority 2: Topics with active weakness flags
    with_flags = [r for r in records if r.weakness_flags]
    if with_flags:
        target = min(with_flags, key=lambda x: x.mastery_score)
        label = CANONICAL_TOPIC_PORTUGUESE.get(
            target.topic_key, target.topic_key.replace("_", " ").title()
        )
        return target.topic_key, label, target.mastery_score

    # Priority 3: Lowest mastery overall among attempted
    any_attempted = [r for r in records if r.attempts_count > 0]
    if any_attempted:
        target = min(any_attempted, key=lambda x: x.mastery_score)
        label = CANONICAL_TOPIC_PORTUGUESE.get(
            target.topic_key, target.topic_key.replace("_", " ").title()
        )
        return target.topic_key, label, target.mastery_score

    # Priority 4: Default canonical topic
    default_key = (
        CANONICAL_CURRICULUM_TOPICS[0][0]
        if CANONICAL_CURRICULUM_TOPICS
        else "1st_declension_nominative"
    )
    label = CANONICAL_TOPIC_PORTUGUESE.get(
        default_key, default_key.replace("_", " ").title()
    )
    return default_key, label, 0.50


@router.post("/generate", response_model=ArenaChallengeResponse)
async def generate_arena_challenge(
    payload: ArenaGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Generate a focused 3-flashcard combat round in the Arena targeting student weaknesses.

    Uses a restricted mini-prompt (< 150 tokens) with deterministic fallback.
    """
    topic_key, topic_label, current_mastery = await _select_target_topic(
        db, current_user.id, payload.topic_key
    )
    vulnerability_score = round(max(0.0, 1.0 - current_mastery), 2)

    generated_cards: list[ArenaFlashcard] = []

    # 1. Attempt generation via Mini Prompt (LLM Router / Tutor)
    llm = get_llm_for_role(ModelRole.ROUTER) or get_llm_for_role(ModelRole.TUTOR)
    if llm:
        system_prompt = (
            f"Você é o Magister Latium Arena.\n"
            f"Gere exatamente 3 flashcards ultracurtos em Latim focados exclusivamente no tópico '{topic_label}' ({topic_key}).\n"
            f"Cada cartão deve ter uma frase curta em Latim clássico, tradução direta em Português e uma dica de gramática.\n"
            f'Retorne estritamente em JSON válido: {{"cards": [{{"id": 1, "latin": "...", "translation": "...", "hint": "..."}}]}}\n'
            f"Máximo de 130 tokens. Sem explicações ou saudações."
        )
        try:
            # Bind max_tokens to 150 for strict cost containment
            bounded_llm = (
                llm.bind(max_tokens=150) if hasattr(llm, "bind") else llm
            )
            response = await bounded_llm.ainvoke(
                [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"Gere 3 flashcards curtos para o tópico: {topic_label}.",
                    },
                ]
            )
            raw_text = (
                response.content
                if hasattr(response, "content")
                else str(response)
            )

            # Strip markdown fences if present
            clean_json = re.sub(
                r"^```json\s*|\s*```$", "", raw_text.strip(), flags=re.MULTILINE
            )
            parsed = json.loads(clean_json)

            cards_list = parsed.get("cards", [])
            for idx, c in enumerate(cards_list[:3], start=1):
                latin = c.get("latin", "").strip()
                trans = c.get("translation", "").strip()
                hint = c.get("hint", "").strip()
                if latin and trans:
                    audio_hash = generate_audio_hash(latin, "onyx")
                    generated_cards.append(
                        ArenaFlashcard(
                            id=idx,
                            latin=latin,
                            translation=trans,
                            hint=hint,
                            audio_url=f"/api/v1/media/audio/{audio_hash}",
                        )
                    )
        except Exception as exc:
            logger.warning(
                "Mini-prompt LLM generation skipped or failed (%s); using canonical fallback.",
                exc,
            )

    # 2. Canonical deterministic fallback if LLM was unavailable or produced invalid output
    if len(generated_cards) < 3:
        deck_source = CANONICAL_MINI_DECKS.get(
            topic_key, CANONICAL_MINI_DECKS["1st_declension_accusative"]
        )
        generated_cards = []
        for idx, c in enumerate(deck_source[:3], start=1):
            audio_hash = generate_audio_hash(c["latin"], "onyx")
            generated_cards.append(
                ArenaFlashcard(
                    id=idx,
                    latin=c["latin"],
                    translation=c["translation"],
                    hint=c.get("hint", ""),
                    audio_url=f"/api/v1/media/audio/{audio_hash}",
                )
            )

    return ArenaChallengeResponse(
        challenge_id=str(uuid.uuid4()),
        topic_key=topic_key,
        topic_label=topic_label,
        current_mastery=current_mastery,
        vulnerability_score=vulnerability_score,
        cards=generated_cards,
    )


@router.post("/evaluate", response_model=ArenaEvaluationResponse)
async def evaluate_arena_card(
    payload: ArenaEvaluationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Evaluate student's flashcard response and dynamically update EMA proficiency in real-time."""
    student_clean = payload.student_answer.strip().lower()
    expected_clean = payload.expected_answer.strip().lower()

    # Query current mastery
    prof_query = select(StudentTopicProficiency).where(
        StudentTopicProficiency.user_id == current_user.id,
        StudentTopicProficiency.topic_key == payload.topic_key,
    )
    prof_res = (await db.execute(prof_query)).scalar_one_or_none()
    prev_mastery = prof_res.mastery_score if prof_res else 0.50

    is_correct = False
    score = 0
    feedback = ""

    # --- Layer 1: Heuristic string/regex match (Zero LLM cost) ---
    norm_student = re.sub(r"[^\w\s]", "", student_clean)
    norm_expected = re.sub(r"[^\w\s]", "", expected_clean)

    if (
        norm_student == norm_expected
        or student_clean in expected_clean
        or expected_clean in student_clean
    ):
        is_correct = True
        score = 100
        feedback = "Optime! Tradução exata e impecável."
    else:
        # Check token overlap
        student_words = set(norm_student.split())
        expected_words = set(norm_expected.split())
        overlap = len(student_words.intersection(expected_words))

        if len(expected_words) > 0 and (overlap / len(expected_words)) >= 0.70:
            is_correct = True
            score = 90
            feedback = "Bene! Tradução substancialmente correta."
        else:
            # --- Layer 2: Censor Míni (< 40 tokens) for semantic nuances ---
            evaluator_llm = get_llm_for_role(
                ModelRole.EVALUATOR
            ) or get_llm_for_role(ModelRole.ROUTER)
            if evaluator_llm:
                eval_prompt = (
                    f"Você é o Censor Latium Míni. Avalie a tradução em português do aluno.\n"
                    f"Frase em latim: '{payload.latin}'\n"
                    f"Tradução esperada: '{payload.expected_answer}'\n"
                    f"Resposta do aluno: '{payload.student_answer}'\n"
                    f"A tradução do aluno é aceitável em português?\n"
                    f'Responda em JSON estrito: {{"is_correct": boolean, "score": int, "feedback": "uma frase curta"}}\n'
                    f"Máximo de 35 tokens."
                )
                try:
                    bounded_eval = (
                        evaluator_llm.bind(max_tokens=50)
                        if hasattr(evaluator_llm, "bind")
                        else evaluator_llm
                    )
                    eval_resp = await bounded_eval.ainvoke(
                        [{"role": "system", "content": eval_prompt}]
                    )
                    raw_eval = (
                        eval_resp.content
                        if hasattr(eval_resp, "content")
                        else str(eval_resp)
                    )
                    clean_eval = re.sub(
                        r"^```json\s*|\s*```$",
                        "",
                        raw_eval.strip(),
                        flags=re.MULTILINE,
                    )
                    eval_json = json.loads(clean_eval)
                    is_correct = bool(eval_json.get("is_correct", False))
                    score = int(eval_json.get("score", 100 if is_correct else 30))
                    feedback = eval_json.get(
                        "feedback",
                        "Tradução correta!" if is_correct else "Atenção ao significado exato.",
                    )
                except Exception as exc:
                    logger.warning("Censor Míni fallback triggered: %s", exc)
                    is_correct = False
                    score = 40
                    feedback = f"Gabarito esperado: '{payload.expected_answer}'."
            else:
                is_correct = False
                score = 30
                feedback = f"Gabarito esperado: '{payload.expected_answer}'."

    # --- Live EMA Update: update student proficiency in PostgreSQL ---
    detected_errs = [payload.topic_key] if not is_correct else None
    updated_records = await record_exercise_result(
        db=db,
        user_id=current_user.id,
        topic_keys=[payload.topic_key],
        score=score,
        detected_errors=detected_errs,
    )

    new_mastery = (
        updated_records[0].mastery_score if updated_records else prev_mastery
    )

    return ArenaEvaluationResponse(
        card_id=payload.card_id,
        is_correct=is_correct,
        score=score,
        feedback=feedback,
        previous_mastery=prev_mastery,
        new_mastery=new_mastery,
    )

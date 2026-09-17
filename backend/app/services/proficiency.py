import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.progress import StudentTopicProficiency
from app.schemas.proficiency import (
    StudentProficiencyProfileResponse,
    TopicProficiencyItem,
)

logger = logging.getLogger(__name__)

CANONICAL_CURRICULUM_TOPICS: list[tuple[str, str]] = [
    # Módulo I
    ("1st_declension_nominative", "morphology"),
    ("verb_esse_present", "verbs"),
    ("questions_with_ne", "syntax"),
    ("1st_declension_accusative", "syntax"),
    ("1st_declension_genitive", "syntax"),
    ("preposition_in_ablative", "syntax"),
    ("vocabulary_family", "vocabulary"),
    # Módulo II
    ("2nd_declension_masculine", "morphology"),
    ("noun_adjective_agreement", "agreement"),
    ("vocative_case", "syntax"),
    ("regular_conjugations", "verbs"),
    ("verb_personal_endings", "morphology"),
]

# Baseline for backward-compatibility
CANONICAL_BASELINE_TOPICS: list[tuple[str, str]] = CANONICAL_CURRICULUM_TOPICS

CANONICAL_TOPIC_ALIASES: dict[str, str] = {
    # 1st Declension Nominative
    "1st_declension_nominative": "1st_declension_nominative",
    "1ª declinação (-a, -ae)": "1st_declension_nominative",
    "1a declinacao (-a, -ae)": "1st_declension_nominative",
    "caso nominativo": "1st_declension_nominative",
    "nominativo": "1st_declension_nominative",
    # Verb esse
    "verb_esse_present": "verb_esse_present",
    "est / sunt": "verb_esse_present",
    "verbo esse": "verb_esse_present",
    # Questions with -ne
    "questions_with_ne": "questions_with_ne",
    "perguntas com -ne": "questions_with_ne",
    # 1st Declension Accusative
    "1st_declension_accusative": "1st_declension_accusative",
    "caso acusativo (-am)": "1st_declension_accusative",
    "caso acusativo": "1st_declension_accusative",
    "acusativo": "1st_declension_accusative",
    # 1st Declension Genitive
    "1st_declension_genitive": "1st_declension_genitive",
    "caso genitivo (-ae)": "1st_declension_genitive",
    "caso genitivo": "1st_declension_genitive",
    "genitivo": "1st_declension_genitive",
    # Preposition in + ablative
    "preposition_in_ablative": "preposition_in_ablative",
    "preposição in + ablativo": "preposition_in_ablative",
    "preposicao in + ablativo": "preposition_in_ablative",
    # Vocabulary family
    "vocabulary_family": "vocabulary_family",
    "vocabulário familiar": "vocabulary_family",
    "vocabulario familiar": "vocabulary_family",
    # 2nd Declension Masculine
    "2nd_declension_masculine": "2nd_declension_masculine",
    "2ª declinação masculina (-us, -i)": "2nd_declension_masculine",
    "2a declinacao masculina (-us, -i)": "2nd_declension_masculine",
    # Noun-adjective agreement
    "noun_adjective_agreement": "noun_adjective_agreement",
    "adjective_agreement_feminine": "noun_adjective_agreement",
    "concordância nominal": "noun_adjective_agreement",
    "concordancia nominal": "noun_adjective_agreement",
    # Vocative
    "vocative_case": "vocative_case",
    "caso vocativo": "vocative_case",
    "vocativo": "vocative_case",
    # Regular conjugations
    "regular_conjugations": "regular_conjugations",
    "conjugações regulares (-are, -ere, -ere, -ire)": "regular_conjugations",
    "conjugaçoes regulares (-are, -ere, -ere, -ire)": "regular_conjugations",
    # Personal endings
    "verb_personal_endings": "verb_personal_endings",
    "desinências pessoais (-o, -s, -t, -mus, -tis, -nt)": "verb_personal_endings",
    "desinencias pessoais (-o, -s, -t, -mus, -tis, -nt)": "verb_personal_endings",
    # Word order
    "basic_latin_word_order": "basic_latin_word_order",
}


def normalize_topic_key(raw_key: str) -> str:
    """Normalize any topic string or canonical variation into the canonical topic_key."""
    cleaned = raw_key.strip().lower()
    return CANONICAL_TOPIC_ALIASES.get(cleaned, cleaned)




CANONICAL_TOPIC_PORTUGUESE: dict[str, str] = {
    "1st_declension_nominative": "1ª Declinação (Caso Nominativo)",
    "verb_esse_present": "Verbo Esse (Presente do Indicativo)",
    "questions_with_ne": "Interrogações Clássicas (-ne)",
    "1st_declension_accusative": "1ª Declinação (Caso Acusativo)",
    "1st_declension_genitive": "1ª Declinação (Caso Genitivo)",
    "preposition_in_ablative": "Preposição In + Ablativo",
    "vocabulary_family": "Vocabulário Familiar Romano",
    "2nd_declension_masculine": "2ª Declinação Masculina (-us, -i)",
    "noun_adjective_agreement": "Concordância Nominal",
    "vocative_case": "Caso Vocativo",
    "regular_conjugations": "Conjugações Verbais Regulares",
    "verb_personal_endings": "Desinências Pessoais Ativas",
    "adjective_agreement_feminine": "Concordância Adjetival Feminina",
    "basic_latin_word_order": "Ordem Canônica das Palavras (SOV)",
}


async def get_or_create_student_topic(
    db: AsyncSession,
    user_id: uuid.UUID,
    topic_key: str,
    category: str = "morphosyntax",
) -> StudentTopicProficiency:
    """Retrieve or initialize proficiency tracking for a specific topic."""
    query = select(StudentTopicProficiency).where(
        StudentTopicProficiency.user_id == user_id,
        StudentTopicProficiency.topic_key == topic_key,
    )
    result = await db.execute(query)
    prof = result.scalar_one_or_none()

    if prof is None:
        prof = StudentTopicProficiency(
            user_id=user_id,
            topic_key=topic_key,
            category=category,
            mastery_score=0.50,
            attempts_count=0,
            correct_count=0,
            consecutive_successes=0,
            weakness_flags=[],
            last_evaluated_at=datetime.now(UTC),
        )
        db.add(prof)
        await db.flush()
    return prof


async def record_exercise_result(
    db: AsyncSession,
    user_id: uuid.UUID,
    topic_keys: list[str],
    score: int,
    detected_errors: list[str] | None = None,
) -> list[StudentTopicProficiency]:
    """Update student topic proficiency using adaptive Exponential Moving Average (EMA).

    Formula: M_(t+1) = M_t + alpha * (normalized_score - M_t)
    """
    normalized_keys: list[str] = []
    for k in topic_keys:
        norm = normalize_topic_key(k)
        if norm and norm != "general_latin_syntax" and norm not in normalized_keys:
            normalized_keys.append(norm)

    if not normalized_keys:
        # Fallback strictly to canonical baseline topic (never create phantom topics)
        normalized_keys = ["1st_declension_nominative"]

    normalized_score = max(0.0, min(1.0, score / 100.0))
    updated_records: list[StudentTopicProficiency] = []

    for topic_key in normalized_keys:
        prof = await get_or_create_student_topic(db, user_id, topic_key)
        prof.attempts_count += 1
        prof.last_evaluated_at = datetime.now(UTC)

        # Asymmetric learning rate alpha: higher penalty for errors to trigger reinforcement
        if normalized_score >= 0.85:
            alpha = 0.20
            prof.correct_count += 1
            prof.consecutive_successes += 1
            # Gradually prune resolved weaknesses if consecutive successes >= 3
            if prof.consecutive_successes >= 3 and prof.weakness_flags:
                prof.weakness_flags = prof.weakness_flags[1:]
        elif normalized_score < 0.60:
            alpha = 0.35
            prof.consecutive_successes = 0
            if detected_errors:
                existing = set(prof.weakness_flags)
                for err in detected_errors:
                    if err not in existing:
                        prof.weakness_flags.append(err)
        else:
            alpha = 0.25

        # Update mastery score bounded in [0.05, 0.99]
        new_mastery = prof.mastery_score + alpha * (
            normalized_score - prof.mastery_score
        )
        prof.mastery_score = round(max(0.05, min(0.99, new_mastery)), 3)
        updated_records.append(prof)

    await db.commit()
    return updated_records


async def get_student_proficiency_profile(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> StudentProficiencyProfileResponse:
    """Compile the complete multi-topic proficiency profile for a student."""
    query = (
        select(StudentTopicProficiency)
        .where(StudentTopicProficiency.user_id == user_id)
        .order_by(StudentTopicProficiency.mastery_score.asc())
    )
    result = await db.execute(query)
    raw_records = list(result.scalars().all())

    # Purge any ghost topics (like 'general_latin_syntax') immediately
    records: list[StudentTopicProficiency] = []
    ghosts_found = False
    for r in raw_records:
        if r.topic_key == "general_latin_syntax":
            await db.delete(r)
            ghosts_found = True
        else:
            records.append(r)

    # Ensure all canonical curriculum topics exist for the student
    existing_keys = {r.topic_key for r in records}
    topics_added = False
    for topic_key, category in CANONICAL_CURRICULUM_TOPICS:
        if topic_key not in existing_keys:
            p = StudentTopicProficiency(
                user_id=user_id,
                topic_key=topic_key,
                category=category,
                mastery_score=0.50,
                attempts_count=0,
                correct_count=0,
                consecutive_successes=0,
                weakness_flags=[],
                last_evaluated_at=datetime.now(UTC),
            )
            db.add(p)
            records.append(p)
            topics_added = True

    if ghosts_found or topics_added:
        await db.commit()

    topic_items: list[TopicProficiencyItem] = []
    mastered: list[str] = []
    vulnerable: list[str] = []
    total_attempted_mastery = 0.0

    for rec in records:
        if rec.attempts_count == 0:
            # Unstarted topics contribute 0.0 demonstrated mastery
            display_score = 0.0
            status = "in_progress"
        else:
            display_score = rec.mastery_score
            total_attempted_mastery += rec.mastery_score
            if rec.mastery_score >= 0.80:
                status = "mastered"
                mastered.append(rec.topic_key)
            elif rec.mastery_score < 0.50:
                status = "vulnerable"
                vulnerable.append(rec.topic_key)
            else:
                status = "in_progress"

        topic_items.append(
            TopicProficiencyItem(
                topic_key=rec.topic_key,
                category=rec.category,
                mastery_score=display_score,
                attempts_count=rec.attempts_count,
                correct_count=rec.correct_count,
                consecutive_successes=rec.consecutive_successes,
                status=status,
                weakness_flags=rec.weakness_flags or [],
            )
        )

    # Proportional calculation against the full canonical curriculum scope (Modules I & II)
    curriculum_scope = max(len(CANONICAL_CURRICULUM_TOPICS), len(records))
    overall_mastery = (
        round(total_attempted_mastery / curriculum_scope, 2)
        if curriculum_scope > 0
        else 0.0
    )
    overall_mastery = min(1.0, max(0.0, overall_mastery))

    if vulnerable:
        vulnerable_human = [
            CANONICAL_TOPIC_PORTUGUESE.get(k, k) for k in vulnerable[:3]
        ]
        focus_text = f"Reforço intensivo em: {', '.join(vulnerable_human)}."
    elif mastered:
        focus_text = "Fundamentos consolidados. Pronto para construções e orações subordinadas mais desafiadoras."
    elif total_attempted_mastery > 0:
        focus_text = "Estágio de nivelamento: continue praticando as desinências e vocabulário das primeiras lições."
    else:
        focus_text = "Início da jornada clássica: complete a primeira lição para inaugurar sua maestria."

    return StudentProficiencyProfileResponse(
        user_id=user_id,
        overall_mastery=overall_mastery,
        total_topics_tracked=len(records),
        mastered_topics=mastered,
        vulnerable_topics=vulnerable,
        topic_details=topic_items,
        recommended_focus=focus_text,
    )


def format_proficiency_for_prompt(profile: StudentProficiencyProfileResponse) -> str:
    """Format adaptive student proficiency directives for injection into the lesson generation prompt."""
    mastered_str = (
        ", ".join(profile.mastered_topics)
        if profile.mastered_topics
        else "Nenhum tópico em nível magistral ainda"
    )
    vulnerable_str = (
        ", ".join(profile.vulnerable_topics)
        if profile.vulnerable_topics
        else "Nenhuma fraqueza crítica detectada"
    )

    weaknesses_detail: list[str] = []
    for item in profile.topic_details:
        if item.status == "vulnerable":
            flags_desc = (
                f" (Fragilidades: {', '.join(item.weakness_flags)})"
                if item.weakness_flags
                else ""
            )
            weaknesses_detail.append(
                f"- {item.topic_key}: {int(item.mastery_score * 100)}% de maestria{flags_desc}"
            )

    weaknesses_block = (
        "\n".join(weaknesses_detail)
        if weaknesses_detail
        else "- Nenhuma fragilidade crítica identificada."
    )

    return f"""[PERFIL ADAPTATIVO DO ALUNO - PROFICIÊNCIA ATUAL: {int(profile.overall_mastery * 100)}%]
• Tópicos Dominados: {mastered_str}
• Tópicos com Fragilidades Identificadas: {vulnerable_str}
• Detalhamento das Vulnerabilidades:
{weaknesses_block}
• Foco Recomendado pelo Censor: {profile.recommended_focus}

DIRETRIZ PEDAGÓGICA ADAPTATIVA:
Se houver tópicos vulneráveis listados acima, adapte a lição:
1. Reforce a teoria dos tópicos com menor maestria através de contrastes claros.
2. Dê destaque nos exemplos às desinências ou regras onde o aluno hesita.
3. Elabore pelo menos um exercício focado em consolidar essas lacunas identificadas."""

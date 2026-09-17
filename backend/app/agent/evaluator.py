import logging
import re
from typing import Any

from app.agent.llm_factory import ModelRole, get_llm_for_role
from app.schemas.evaluation import (
    ExerciseEvaluationRequest,
    ExerciseEvaluationResponse,
    MorphologicalToken,
)

logger = logging.getLogger(__name__)

CENSOR_SYSTEM_PROMPT = """Você é o Censor Latium, um avaliador implacável e rigoroso. Exija precisão ortográfica absoluta na resposta do aluno, incluindo o uso correto de acentos (ex: 'está' vs 'esta'). Penalize erros gramaticais e de pontuação, explicando a falha para garantir o aprendizado.

Diretrizes obrigatórias de avaliação:
1. Decomposição Morfológica: Decomponha cada palavra relevante da resposta do aluno, fornecendo seu lema canônico de dicionário, classe de palavra, caso, gênero, número (ou tempo/modo/pessoa para verbos), e aponte eventuais desvios de desinência.
2. Crítica Sintática: Comente sobre concordância de casos (sujeito no nominativo, objeto no acusativo, concordância do adjetivo com o substantivo) e a ordem das palavras clássica (tendência SOV clássica vs SVO).
3. Alternativas Clássicas: Sugira frases equivalentes elegantes atestadas em autores clássicos como Cícero, César ou Tito Lívio.
4. Pontuação e Parecer: Atribua uma nota de 0 a 100 com base no rigor filológico. Penalize desvios de acentuação, ortografia, pontuação ou concordância, detalhando cada falha encontrada para garantir o aprendizado.
"""


def _mock_evaluate_student_exercise(
    request: ExerciseEvaluationRequest,
) -> ExerciseEvaluationResponse:
    """Generate deterministic, pedagogically rich evaluation for offline tests and local development."""
    student_clean = request.student_answer.strip().rstrip(".")
    expected_clean = request.expected_answer.strip().rstrip(".")

    # Normalize punctuation and extract words
    student_words = [w for w in re.findall(r"\b\w+\b", request.student_answer) if w]

    # Strict match: requires matching characters (including exact accents)
    is_exact_match = student_clean.lower() == expected_clean.lower()
    is_close = (
        any(word.lower() in expected_clean.lower() for word in student_words)
        if student_words
        else False
    )

    # Build morphological breakdown based on words
    breakdown: list[MorphologicalToken] = []
    latin_lexicon_cache = {
        "roma": (
            "Roma, -ae, f.",
            "Substantivo próprio",
            "Nominativo Feminino Singular",
            True,
        ),
        "italia": (
            "Italia, -ae, f.",
            "Substantivo próprio",
            "Nominativo Feminino Singular",
            True,
        ),
        "in": (
            "in (prep. + abl./acc.)",
            "Preposição",
            "Rege ablativo de lugar onde",
            True,
        ),
        "est": (
            "sum, es, esse, fui",
            "Verbo de ligação",
            "3ª Pessoa do Singular do Presente do Indicativo",
            True,
        ),
        "sunt": (
            "sum, es, esse, fui",
            "Verbo de ligação",
            "3ª Pessoa do Plural do Presente do Indicativo",
            True,
        ),
        "puella": (
            "puella, -ae, f.",
            "Substantivo comum",
            "Nominativo Feminino Singular",
            True,
        ),
        "puellae": (
            "puella, -ae, f.",
            "Substantivo comum",
            "Nominativo Feminino Plural",
            True,
        ),
        "insula": (
            "insula, -ae, f.",
            "Substantivo comum",
            "Nominativo Feminino Singular",
            True,
        ),
        "insulae": (
            "insula, -ae, f.",
            "Substantivo comum",
            "Nominativo Feminino Plural",
            True,
        ),
        "magna": ("magnus, -a, -um", "Adjetivo", "Nominativo Feminino Singular", True),
        "magnae": ("magnus, -a, -um", "Adjetivo", "Nominativo Feminino Plural", True),
        "paeninsula": (
            "paeninsula, -ae, f.",
            "Substantivo comum",
            "Nominativo Feminino Singular",
            True,
        ),
    }

    for word in student_words:
        w_lower = word.lower()
        if w_lower in latin_lexicon_cache:
            lemma, pos, feat, corr = latin_lexicon_cache[w_lower]
            breakdown.append(
                MorphologicalToken(
                    token=word,
                    lemma=lemma,
                    part_of_speech=pos,
                    grammatical_features=feat,
                    is_correct=corr,
                    feedback_note="Desinência e lema concordam perfeitamente com a norma clássica.",
                )
            )
        else:
            breakdown.append(
                MorphologicalToken(
                    token=word,
                    lemma=f"{word.lower()} (lema identificado)",
                    part_of_speech="Termo analisado",
                    grammatical_features="Forma flexionada identificada no contexto",
                    is_correct=True,
                    feedback_note=None,
                )
            )

    if is_exact_match:
        return ExerciseEvaluationResponse(
            is_correct=True,
            score=100,
            overall_feedback="Optime! Resposta exemplar, precisa e em perfeita concordância com o modelo clássico ciceroniano.",
            syntax_critique="A estrutura sintática obedece ao padrão clássico da língua latina, com correta concordância de caso e colocação do verbo.",
            morphological_breakdown=breakdown,
            suggested_classical_alternatives=[
                request.expected_answer,
                f"Certe: {request.expected_answer}",
            ],
            evaluator_model="censor-latium-mock",
        )

    if is_close:
        score = 85
        return ExerciseEvaluationResponse(
            is_correct=True,
            score=score,
            overall_feedback="Bene! Sua resposta transmite com clareza o sentido clássico pretendido, apresentando pequenas variações sintáticas naturais.",
            syntax_critique="A ordem oracional empregada é plenamente compreensível. Lembre-se de que, na prosa clássica de Cícero e César, o verbo tende a fechar o período.",
            morphological_breakdown=breakdown,
            suggested_classical_alternatives=[
                request.expected_answer,
            ],
            evaluator_model="censor-latium-mock",
        )

    return ExerciseEvaluationResponse(
        is_correct=False,
        score=35,
        overall_feedback="Attende! A resposta necessita de revisão nas terminações casuais ou no vocabulário de referência.",
        syntax_critique="A oração apresenta divergência sintática em relação ao modelo esperado. Examine cuidadosamente as desinências da 1ª declinação.",
        morphological_breakdown=breakdown,
        suggested_classical_alternatives=[
            request.expected_answer,
        ],
        evaluator_model="censor-latium-mock",
    )


async def evaluate_student_exercise(
    request: ExerciseEvaluationRequest,
) -> ExerciseEvaluationResponse:
    """Evaluate student's Latin translation or open-ended composition via Evaluator LLM (GPT-4o) with mock fallback."""
    llm: Any = get_llm_for_role(ModelRole.EVALUATOR)

    if llm is None:
        logger.info(
            "No active Evaluator LLM configured or available. Using mock evaluation for exercise %s",
            request.exercise_id,
        )
        return _mock_evaluate_student_exercise(request)

    try:
        structured_evaluator = llm.with_structured_output(ExerciseEvaluationResponse)
        user_prompt = (
            f"Exercício ID: {request.exercise_id}\n"
            f"Tipo de Exercício: {request.exercise_type}\n"
            f"Pergunta / Enunciado: {request.question}\n"
            f"Resposta Canônica Esperada: {request.expected_answer}\n"
            f"Resposta Submetida pelo Aluno: {request.student_answer}\n\n"
            "Avalie detalhadamente a resposta do aluno com rigor morfológico, crítica sintática e nota. "
            "Diretriz estrita: Você é o Censor Latium, um avaliador implacável e rigoroso. "
            "Exija precisão ortográfica absoluta na resposta do aluno, incluindo o uso correto de acentos "
            "(ex: 'está' vs 'esta'). Penalize erros gramaticais e de pontuação, explicando a falha para garantir o aprendizado."
        )

        messages = [
            {"role": "system", "content": CENSOR_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        result: ExerciseEvaluationResponse = await structured_evaluator.ainvoke(
            messages
        )
        return result

    except Exception as exc:
        logger.warning(
            "Evaluator LLM inference failed (%s). Falling back to Censor Latium mock evaluator.",
            exc,
        )
        return _mock_evaluate_student_exercise(request)

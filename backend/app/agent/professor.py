import logging
from typing import Any, TypedDict

from app.schemas.lesson import (
    LatinExample,
    LessonContent,
    LessonExercise,
    TheorySection,
    VocabularyItem,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Você é o Magister Latium, um mestre humanista e erudito no ensino da Língua Latina Clássica.
Sua missão pedagógica é ensinar Latim combinando o rigor gramatical tradicional à metodologia indutivo-contextual (inspirada no método de Hans Ørberg / Lingua Latina per se Illustrata).

Diretrizes obrigatórias para a elaboração de cada aula:
1. Teoria: Explique a função dos casos latinos, desinências, concordâncias e sintaxe de maneira viva, clara e elegante.
2. Exemplos: Crie exemplos clássicos autênticos em Latim com tradução rigorosa em Português e notas gramaticais esclarecedoras.
3. Vocabulário: Apresente as palavras sempre com sua entrada canônica de dicionário (ex: 'puella, -ae, f.', 'amare, amo, amavi, amatum') e tradução precisa.
4. Exercícios: Crie exercícios progressivos com enunciados claros, opções desafiadoras e justificativas gramaticais aprofundadas.
5. Dica do Professor: Conclua com um conselho mnemônico ou reflexão etimológica conectando o Latim ao Português moderno.
"""


class TutorState(TypedDict, total=False):
    """Internal state for the Latin Tutor Agent."""

    lesson_id: str
    student_name: str
    module_title: str
    lesson_title: str
    pedagogical_objective: str
    grammar_topics: list[str]
    lesson_content: LessonContent


def _generate_mock_lesson(
    lesson_id: str,
    student_name: str,
    module_title: str,
    lesson_title: str,
    pedagogical_objective: str,
    grammar_topics: list[str],
) -> LessonContent:
    """Generate a high-quality pedagogical Latin lesson deterministically for testing and offline development."""
    return LessonContent(
        lesson_id=lesson_id,
        module_title=module_title,
        lesson_title=lesson_title,
        pedagogical_goal=pedagogical_objective,
        historical_context=(
            f"Salve, {student_name}! Na Roma Antiga sob o principado de Augusto, a língua latina "
            "era o instrumento de unidade jurídica, literária e política do Mediterrâneo."
        ),
        theory_sections=[
            TheorySection(
                topic="A Estrutura do Caso Nominativo na 1ª Declinação",
                explanation=(
                    "No Latim clássico, as funções sintáticas não dependem da ordem das palavras na frase, "
                    "mas sim de suas terminações (casos). Os substantivos da 1ª declinação são predominantemente "
                    "femininos e terminam em '-a' no nominativo singular (sujeito) e em '-ae' no nominativo plural."
                ),
                rule_summary="Singular: -a (puella - a menina) | Plural: -ae (puellae - as meninas)",
            ),
            TheorySection(
                topic="O Verbo de Ligação 'Esse' no Presente",
                explanation=(
                    "O verbo 'esse' (ser, estar, existir) concorda em número com o sujeito. "
                    "Utiliza-se 'est' para a 3ª pessoa do singular e 'sunt' para a 3ª pessoa do plural."
                ),
                rule_summary="Roma in Italia est (Roma está na Itália) | Roma et Sparta in Europa sunt.",
            ),
        ],
        examples=[
            LatinExample(
                latin="Roma in Italia est.",
                translation="Roma está na Itália.",
                grammatical_notes="Roma (nominativo singular feminino, sujeito); est (3ª pessoa do singular do presente).",
            ),
            LatinExample(
                latin="Italia et Graecia in Europa sunt.",
                translation="A Itália e a Grécia estão na Europa.",
                grammatical_notes="Italia et Graecia (sujeito composto coordenado); sunt (verbo na 3ª pessoa do plural).",
            ),
            LatinExample(
                latin="Puella laeta cantat.",
                translation="A menina alegre canta.",
                grammatical_notes="Puella laeta: adjetivo feminino concordando em caso (nominativo), gênero e número.",
            ),
        ],
        vocabulary=[
            VocabularyItem(
                word="puella",
                dictionary_entry="puella, -ae, f.",
                grammatical_class="Substantivo feminino de 1ª declinação",
                translation="menina, jovem donzela",
                example_sentence="Puella pulchra in horto est.",
            ),
            VocabularyItem(
                word="insula",
                dictionary_entry="insula, -ae, f.",
                grammatical_class="Substantivo feminino de 1ª declinação",
                translation="ilha (ou bloco de edifícios em Roma)",
                example_sentence="Corsica et Sardinia magnae insulae sunt.",
            ),
            VocabularyItem(
                word="esse",
                dictionary_entry="sum, es, esse, fui",
                grammatical_class="Verbo irregular de ligação",
                translation="ser, estar, existir",
                example_sentence="Roma caput mundi est.",
            ),
        ],
        exercises=[
            LessonExercise(
                id=1,
                exercise_type="multiple_choice",
                instruction="Complete a lacuna com a forma correta do verbo 'esse':",
                question="Sicilia et Creta insulae ____.",
                options=["est", "sunt", "esse", "sum"],
                correct_answer="sunt",
                explanation=(
                    "O sujeito é composto ('Sicilia et Creta'), exigindo o verbo de ligação "
                    "na 3ª pessoa do plural ('sunt')."
                ),
            ),
            LessonExercise(
                id=2,
                exercise_type="fill_blank",
                instruction="Complete com a terminação correta do nominativo plural da 1ª declinação:",
                question="Multae puell__ in via ambulant.",
                options=["ae", "a", "am", "as"],
                correct_answer="ae",
                explanation=(
                    "O adjetivo 'multae' indica feminino plural; portanto, o substantivo "
                    "deve receber a desinência '-ae' (puellae)."
                ),
            ),
            LessonExercise(
                id=3,
                exercise_type="translation",
                instruction="Traduza a oração latina para o português:",
                question="Italia paeninsula est.",
                options=None,
                correct_answer="A Itália é uma península.",
                explanation=(
                    "'Italia' é o sujeito (nominativo) e 'paeninsula' atua como predicativo do sujeito, "
                    "ambos no nominativo singular feminino."
                ),
            ),
        ],
        teacher_tip=(
            "Conselho do Magister: Observe que a desinência '-a' da 1ª declinação deu origem à quase totalidade "
            "dos substantivos femininos terminados em '-a' no Português moderno (porta, vida, rosa, terra). "
            "Aprender Latim é redescobrir as raízes da sua própria língua materna!"
        ),
    )


async def generate_lesson_for_student(
    lesson_id: str,
    student_name: str,
    module_title: str,
    lesson_title: str,
    pedagogical_objective: str,
    grammar_topics: list[str],
    library_context: str | None = None,
) -> LessonContent:
    """Generate structured lesson using LangGraph/LangChain or mock provider fallback."""
    from app.agent.llm_factory import ModelRole, get_llm_for_role

    llm: Any = get_llm_for_role(ModelRole.TUTOR)

    if llm is None:
        logger.info("Using mock Latin tutor generator for lesson: %s", lesson_title)
        return _generate_mock_lesson(
            lesson_id=lesson_id,
            student_name=student_name,
            module_title=module_title,
            lesson_title=lesson_title,
            pedagogical_objective=pedagogical_objective,
            grammar_topics=grammar_topics,
        )

    # Online AI generation via LangChain structured output
    try:
        user_prompt = (
            f"Elabore uma aula completa para o aluno {student_name}.\n"
            f"Módulo: {module_title}\n"
            f"Lição: {lesson_title}\n"
            f"Objetivo pedagógico: {pedagogical_objective}\n"
            f"Tópicos gramaticais a cobrir: {', '.join(grammar_topics)}\n"
            f"ID da lição: {lesson_id}\n"
        )

        if library_context:
            user_prompt += (
                f"\nFragmentos Canônicos da Biblioteca de Alexandria (RAG):\n"
                f"{library_context}\n"
                "Incorpore com elegância trechos destes fragmentos autênticos para exemplificar a teoria e os exercícios da aula.\n"
            )

        structured_llm = llm.with_structured_output(LessonContent)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
        response: LessonContent = await structured_llm.ainvoke(messages)
        return response

    except Exception as exc:
        logger.warning(
            "External LLM generation failed (%s). Falling back to mock generator.",
            exc,
        )

    return _generate_mock_lesson(
        lesson_id=lesson_id,
        student_name=student_name,
        module_title=module_title,
        lesson_title=lesson_title,
        pedagogical_objective=pedagogical_objective,
        grammar_topics=grammar_topics,
    )

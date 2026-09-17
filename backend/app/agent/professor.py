import logging
from typing import Any, TypedDict

from app.core.config import settings
from app.schemas.lesson import (
    HistoricalTrivia,
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
6. Proteção de Lacunas (Anti-Leak): Em exercícios (especialmente fill_blank e multiple_choice), JAMAIS coloque a resposta esperada (correct_answer) no campo 'question' nem no campo 'instruction'. O campo 'question' deve conter a frase latina com a lacuna indicada por '____' (ex: 'Sicilia et Creta insulae ____.') e nunca a palavra-alvo isolada ou preenchida antes da resposta do aluno.
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
    title_lower = lesson_title.lower()
    topics_str = " ".join(grammar_topics).lower()

    # Chapter II: Familia Romana & Acusativo / Genitivo
    if "acusativo" in title_lower or "familia" in title_lower or "acusativo" in topics_str:
        return LessonContent(
            lesson_id=lesson_id,
            module_title=module_title,
            lesson_title=lesson_title,
            pedagogical_goal=pedagogical_objective,
            historical_context=(
                f"Salve, {student_name}! Na sociedade romana clássica, a 'familia' designava não apenas "
                "os laços de sangue, mas toda a casa sob a autoridade do 'pater familias', incluindo filhos, esposa e servos."
            ),
            theory_sections=[
                TheorySection(
                    topic="O Caso Acusativo: O Alvo da Ação Verbal",
                    explanation=(
                        "O caso acusativo indica o objeto direto que recebe a ação de um verbo transitivo. "
                        "Na 1ª declinação, o singular termina em '-am'. Por exemplo, 'Puella cantat' (nominativo, a menina canta), "
                        "mas 'Pater puellam videt' (acusativo, o pai vê a menina)."
                    ),
                    rule_summary="Nominativo: -a (sujeito) | Acusativo: -am (objeto direto singular)",
                ),
                TheorySection(
                    topic="O Caso Genitivo: A Relação de Posse",
                    explanation=(
                        "O caso genitivo corresponde ao adjunto adnominal restritivo de posse ('de quem'). "
                        "Na 1ª declinação singular, a desinência é '-ae'. Ex: 'Rosa puellae' (A rosa da menina)."
                    ),
                    rule_summary="Genitivo singular: -ae (de posse: villa dominae - a casa da senhora)",
                ),
            ],
            examples=[
                LatinExample(
                    latin="Iulius magnam familiam habet.",
                    translation="Júlio tem uma grande família.",
                    grammatical_notes="Iulius (nominativo sujeito); magnam familiam (acusativo feminino singular objeto direto de habet).",
                ),
                LatinExample(
                    latin="Mater filiam amat.",
                    translation="A mãe ama a filha.",
                    grammatical_notes="Mater (sujeito); filiam (acusativo singular de filia); amat (verbo transitivo direto).",
                ),
                LatinExample(
                    latin="Cornelia in villa est.",
                    translation="Cornélia está na casa de campo.",
                    grammatical_notes="in + ablativo (villa): indica localização no espaço ('onde').",
                ),
            ],
            vocabulary=[
                VocabularyItem(
                    word="pater",
                    dictionary_entry="pater, patris, m.",
                    grammatical_class="Substantivo masculino de 3ª declinação",
                    translation="pai, chefe de família",
                    example_sentence="Pater familias in atrio sedet.",
                ),
                VocabularyItem(
                    word="mater",
                    dictionary_entry="mater, matris, f.",
                    grammatical_class="Substantivo feminino de 3ª declinação",
                    translation="mãe",
                    example_sentence="Mater filios suos curat.",
                ),
                VocabularyItem(
                    word="familia",
                    dictionary_entry="familia, -ae, f.",
                    grammatical_class="Substantivo feminino de 1ª declinação",
                    translation="família, casa senhorial",
                    example_sentence="Familia Romana magna est.",
                ),
            ],
            exercises=[
                LessonExercise(
                    id=1,
                    exercise_type="multiple_choice",
                    instruction="Selecione a forma correta do acusativo singular para completar a frase:",
                    question="Pater multas rosas et unam vill__ habet.",
                    options=["am", "ae", "as", "a"],
                    correct_answer="am",
                    explanation="O substantivo 'villa' está atuando como objeto direto singular de 'habet', exigindo a desinência '-am'.",
                ),
                LessonExercise(
                    id=2,
                    exercise_type="fill_blank",
                    instruction="Complete com a terminação do genitivo singular de posse:",
                    question="Filius puell__ in horto ambulat.",
                    options=["ae", "am", "as", "a"],
                    correct_answer="ae",
                    explanation="Expressa a posse ('filho da menina'), logo exige genitivo singular '-ae'.",
                ),
                LessonExercise(
                    id=3,
                    exercise_type="translation",
                    instruction="Traduza a oração latina:",
                    question="Mater filiam amat.",
                    options=None,
                    correct_answer="A mãe ama a filha.",
                    explanation="'Mater' é o sujeito e 'filiam' é o objeto direto no acusativo.",
                ),
            ],
            teacher_tip=(
                "Conselho do Magister: Sempre procure primeiro o verbo da frase. Se o verbo for transitivo direto "
                "(como amare, videre, habere), procure a palavra terminada em '-am' para identificar quem recebe a ação!"
            ),
            historical_trivia=[
                HistoricalTrivia(
                    title="O Pater Familias e a Patria Potestas",
                    fact=(
                        "O pater familias detinha poder legal supremo (patria potestas) sobre todos os membros de sua casa. "
                        "Era responsável não apenas pelos bens, mas pelo culto religioso doméstico aos deuses lares."
                    ),
                    latin_motto_or_phrase="Salus familiae suprema lex esto.",
                    source_reference="Institutas de Gaio / Direito Romano Arcaico",
                ),
            ],
        )

    # Chapter III: Pueri et Viri & 2ª Declinação
    if "2ª declinação" in title_lower or "pueri" in title_lower or "2ª declinação" in topics_str:
        return LessonContent(
            lesson_id=lesson_id,
            module_title=module_title,
            lesson_title=lesson_title,
            pedagogical_goal=pedagogical_objective,
            historical_context=(
                f"Salve, {student_name}! Chegamos à Segunda Declinação, onde predominam substantivos masculinos "
                "que nomeavam os cidadãos, guerreiros e líderes da República e do Império Romano."
            ),
            theory_sections=[
                TheorySection(
                    topic="Substantivos Masculinos da 2ª Declinação (-us, -i)",
                    explanation=(
                        "A segunda declinação caracteriza-se pelo tema em -o-. Os substantivos masculinos terminam "
                        "geralmente em '-us' no nominativo singular e '-i' no nominativo plural. Ex: 'dominus' (o senhor), 'domini' (os senhores)."
                    ),
                    rule_summary="Singular: -us (dominus) | Plural: -i (domini)",
                ),
                TheorySection(
                    topic="O Caso Vocativo: O Chamamento Direto",
                    explanation=(
                        "O vocativo é o caso usado para interpelar ou chamar alguém diretamente. "
                        "Nos nomes masculinos em '-us' da 2ª declinação, o vocativo singular muda para '-e'. Ex: 'O Marce!' (Ó Marco!)."
                    ),
                    rule_summary="Nominativo: Marcus -> Vocativo: Marce | Brutus -> Brute",
                ),
            ],
            examples=[
                LatinExample(
                    latin="Marcus et Quintus pueri Romani sunt.",
                    translation="Marco e Quinto são meninos romanos.",
                    grammatical_notes="Marcus et Quintus (sujeito composto); pueri (predicativo do sujeito no plural).",
                ),
                LatinExample(
                    latin="Dominus servum vocat.",
                    translation="O senhor chama o servo.",
                    grammatical_notes="Dominus (nominativo); servum (acusativo singular masculino em -um).",
                ),
            ],
            vocabulary=[
                VocabularyItem(
                    word="dominus",
                    dictionary_entry="dominus, -i, m.",
                    grammatical_class="Substantivo masculino de 2ª declinação",
                    translation="senhor, proprietário, mestre",
                    example_sentence="Dominus in horto ambulat.",
                ),
                VocabularyItem(
                    word="servus",
                    dictionary_entry="servus, -i, m.",
                    grammatical_class="Substantivo masculino de 2ª declinação",
                    translation="servo, escravo",
                    example_sentence="Servus domino paret.",
                ),
                VocabularyItem(
                    word="amicus",
                    dictionary_entry="amicus, -i, m.",
                    grammatical_class="Substantivo masculino de 2ª declinação",
                    translation="amigo",
                    example_sentence="Marcus amicus meus est.",
                ),
            ],
            exercises=[
                LessonExercise(
                    id=1,
                    exercise_type="multiple_choice",
                    instruction="Qual é a terminação do vocativo singular de 'amicus'?",
                    question="Salve, amic__!",
                    options=["e", "us", "i", "o"],
                    correct_answer="e",
                    explanation="Nomes da 2ª declinação terminados em '-us' fazem o vocativo singular em '-e'.",
                ),
            ],
            teacher_tip="Lembre-se da célebre frase de César: 'Et tu, Brute?' (Até tu, Brutus?), onde Brute é o vocativo de Brutus.",
            historical_trivia=[
                HistoricalTrivia(
                    title="A Relação de Amicitia em Roma",
                    fact=(
                        "A amicitia (amizade) em Roma era uma instituição pública de aliança cívica e lealdade recíproca, "
                        "essencial para a carreira política no cursus honorum."
                    ),
                    latin_motto_or_phrase="Amicus certus in re incerta cernitur.",
                    source_reference="Cícero, De Amicitia",
                ),
            ],
        )

    # Default / Chapter I: Nominativo na 1ª Declinação
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
        historical_trivia=[
            HistoricalTrivia(
                title="O Pão Selado de Pompeia",
                fact=(
                    "Nas escavações arqueológicas de Pompeia, pães carbonizados foram encontrados perfeitamente preservados após a erupção do Vesúvio em 79 d.C. "
                    "Todos continham um selo gravado em latim: 'Celeris Q. Grani Veri servus' (Celer, escravo de Quinto Grânio Vero), comprovando a autoria da fornada!"
                ),
                latin_motto_or_phrase="Panem nostrum cotidianum.",
                source_reference="Escavações Arqueológicas de Pompeia / Museo Archeologico Nazionale di Napoli",
            ),
            HistoricalTrivia(
                title="A Toga Cândida e os Candidatos",
                fact=(
                    "Em Roma, cidadãos que pleiteavam cargos públicos no Senado utilizavam togas alvejadas com pó de giz branco reluzente (toga candida) "
                    "para simbolizar retidão moral e pureza. Daí surgiu a palavra latina 'candidatus', raiz etimológica direta do nosso vocábulo 'candidato'."
                ),
                latin_motto_or_phrase="Candidatus togam candidam gestat.",
                source_reference="Cícero, De Petitione Consulatus",
            ),
        ],
    )


async def generate_lesson_for_student(
    lesson_id: str,
    student_name: str,
    module_title: str,
    lesson_title: str,
    pedagogical_objective: str,
    grammar_topics: list[str],
    library_context: str | None = None,
    adaptive_profile: str | None = None,
) -> LessonContent:
    """Generate structured lesson using LangGraph/LangChain or mock provider fallback."""
    from app.agent.llm_factory import ModelRole, get_llm_for_role

    llm_candidates: list[Any] = []
    primary = get_llm_for_role(ModelRole.TUTOR)
    if primary is not None:
        llm_candidates.append(primary)

    # Fallback to OpenAI gpt-4o-mini if primary is not OpenAI
    if settings.OPENAI_API_KEY:
        try:
            from langchain_openai import ChatOpenAI

            openai_fallback = ChatOpenAI(
                model="gpt-4o-mini",
                api_key=settings.OPENAI_API_KEY,
                temperature=0.3,
            )
            llm_candidates.append(openai_fallback)
        except Exception as exc:
            logger.debug("OpenAI fallback initialization skipped: %s", exc)

    user_prompt = (
        f"Elabore uma aula completa para o aluno {student_name}.\n"
        f"Módulo: {module_title}\n"
        f"Lição: {lesson_title}\n"
        f"Objetivo pedagógico: {pedagogical_objective}\n"
        f"Tópicos gramaticais a cobrir: {', '.join(grammar_topics)}\n"
        f"ID da lição: {lesson_id}\n"
    )

    if adaptive_profile:
        user_prompt += f"\n\n{adaptive_profile}\n"

    if library_context:
        user_prompt += (
            f"\nFragmentos Canônicos da Biblioteca de Alexandria (RAG):\n"
            f"{library_context}\n"
            "Incorpore com elegância trechos destes fragmentos autênticos para exemplificar a teoria e os exercícios da aula.\n"
        )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    for candidate in llm_candidates:
        try:
            structured_llm = candidate.with_structured_output(LessonContent)
            response: LessonContent = await structured_llm.ainvoke(messages)
            logger.info("Successfully generated structured lesson '%s' via LLM", lesson_title)
            return response
        except Exception as exc:
            logger.warning(
                "LLM generation failed on candidate (%s). Trying next candidate.",
                exc,
            )

    logger.info("Using mock Latin tutor generator for lesson: %s", lesson_title)
    return _generate_mock_lesson(
        lesson_id=lesson_id,
        student_name=student_name,
        module_title=module_title,
        lesson_title=lesson_title,
        pedagogical_objective=pedagogical_objective,
        grammar_topics=grammar_topics,
    )

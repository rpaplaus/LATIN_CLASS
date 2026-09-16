from pydantic import BaseModel, Field


class MorphologicalToken(BaseModel):
    """Grammatical analysis of an individual token/word submitted by the student."""

    token: str = Field(description="A palavra ou termo em latim/português analisado")
    lemma: str = Field(
        description="Entrada de dicionário canônica / lema (ex: puella, amare, sum)"
    )
    part_of_speech: str = Field(
        description="Classe morfológica (substantivo, adjetivo, verbo, pronome, advérbio, preposição)"
    )
    grammatical_features: str = Field(
        description="Caso, gênero, número, tempo, modo, pessoa (ex: Nominativo Feminino Singular)"
    )
    is_correct: bool = Field(
        description="Indica se o termo e sua flexão estão corretos no contexto da oração"
    )
    feedback_note: str | None = Field(
        default=None,
        description="Observação filológica ou aviso de desinência incorreta caso haja erro",
    )


class ExerciseEvaluationRequest(BaseModel):
    """Request payload sent when a student submits an open-ended/translation exercise."""

    lesson_id: str = Field(description="Identificador da lição ativa")
    exercise_id: int = Field(description="Identificador numérico do exercício")
    question: str = Field(
        description="Enunciado ou oração original a traduzir/analisar"
    )
    expected_answer: str = Field(
        description="Resposta canônica de referência do Magister"
    )
    student_answer: str = Field(
        description="Texto ou oração redigida pelo aluno para avaliação"
    )
    exercise_type: str = Field(
        default="translation",
        description="Tipo do exercício (translation, fill_blank, composition)",
    )


class ExerciseEvaluationResponse(BaseModel):
    """Structured Latin evaluation result produced by the Evaluator Agent (Censor)."""

    is_correct: bool = Field(
        description="Verdadeiro se a resposta estiver gramaticalmente correta ou substancialmente válida"
    )
    score: int = Field(
        ge=0,
        le=100,
        description="Nota pedagógica de 0 a 100 baseada em critérios clássicos de rigor sintático",
    )
    overall_feedback: str = Field(
        description="Parecer socrático e encorajador do Avaliador sobre a tentativa do aluno"
    )
    syntax_critique: str = Field(
        description="Análise da estrutura sintática e ordem das palavras (ex: SOV clássico vs SVO românico)"
    )
    morphological_breakdown: list[MorphologicalToken] = Field(
        default_factory=list,
        description="Decomposição morfológica palavra a palavra com lematização e casos",
    )
    suggested_classical_alternatives: list[str] = Field(
        default_factory=list,
        description="Variações clássicas elegantes consagradas em textos latinos de Cícero, César ou Virgílio",
    )
    evaluator_model: str = Field(
        description="Identificador do modelo de IA que realizou a correção analítica"
    )

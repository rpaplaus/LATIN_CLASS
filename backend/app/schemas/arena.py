from pydantic import BaseModel, Field


class ArenaFlashcard(BaseModel):
    """An individual adaptive flashcard challenge in the Arena."""

    id: int = Field(description="Identificador sequencial do cartão (1, 2, 3)")
    latin: str = Field(description="Frase ou termo em Latim clássico para o desafio")
    translation: str = Field(description="Tradução canônica esperada em Português")
    hint: str = Field(
        default="",
        description="Dica gramatical ou morfológica sutil para auxiliar o estudante",
    )
    audio_url: str = Field(
        default="",
        description="URL de streaming do áudio MP3 em cache para o termo em latim",
    )


class ArenaGenerateRequest(BaseModel):
    """Payload to request an Arena combat round."""

    topic_key: str | None = Field(
        default=None,
        description="Tópico específico solicitado, ou None para selecionar a maior fraqueza do aluno automaticamente",
    )


class ArenaChallengeResponse(BaseModel):
    """Aggregated response containing 3 focused adaptive flashcards."""

    challenge_id: str = Field(description="UUID da sessão de combate na Arena")
    topic_key: str = Field(description="Chave canônica do tópico gramatical")
    topic_label: str = Field(description="Nome legível do tópico em Português")
    current_mastery: float = Field(description="Pontuação atual de maestria EMA (0.05 a 0.99)")
    vulnerability_score: float = Field(
        description="Grau de vulnerabilidade do aluno no tópico (1.0 - maestria)"
    )
    cards: list[ArenaFlashcard] = Field(
        description="Lista de 3 cartões de flashcards gerados cirurgicamente"
    )


class ArenaEvaluationRequest(BaseModel):
    """Payload to evaluate a student's answer in the Arena."""

    topic_key: str = Field(description="Tópico gramatical sendo remediado")
    card_id: int = Field(description="ID do cartão avaliado")
    latin: str = Field(description="Frase latina do cartão")
    expected_answer: str = Field(description="Resposta ou tradução esperada")
    student_answer: str = Field(description="Resposta submetida pelo estudante")


class ArenaEvaluationResponse(BaseModel):
    """Pedagogical evaluation and updated mastery for an Arena card."""

    card_id: int = Field(description="ID do cartão avaliado")
    is_correct: bool = Field(description="Indica se a resposta foi considerada correta")
    score: int = Field(description="Nota de 0 a 100")
    feedback: str = Field(description="Parecer ultracurto do Censor Latium Míni")
    previous_mastery: float = Field(description="Maestria EMA antes da resposta")
    new_mastery: float = Field(description="Nova maestria EMA recalculada em tempo real")

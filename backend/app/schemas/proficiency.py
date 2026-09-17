import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TopicProficiencyItem(BaseModel):
    """Granular student mastery status on a specific Latin grammar topic."""

    model_config = ConfigDict(from_attributes=True)

    topic_key: str = Field(description="Chave canônica do tópico gramatical")
    category: str = Field(description="Categoria sintática ou morfológica")
    mastery_score: float = Field(
        ge=0.0, le=1.0, description="Nível de maestria do aluno (0.0 a 1.0)"
    )
    attempts_count: int = Field(description="Total de exercícios submetidos")
    correct_count: int = Field(description="Total de acertos")
    consecutive_successes: int = Field(description="Ofensiva de acertos consecutivos")
    status: Literal["mastered", "in_progress", "vulnerable"] = Field(
        description="Classificação pedagógica: 'mastered' (>=0.80), 'in_progress' (0.50-0.79), 'vulnerable' (<0.50)"
    )
    weakness_flags: list[str] = Field(
        default_factory=list,
        description="Padrões de erro e fragilidades detectadas pelo Censor",
    )


class StudentProficiencyProfileResponse(BaseModel):
    """Complete multi-dimensional proficiency profile of a student."""

    user_id: uuid.UUID
    overall_mastery: float = Field(
        description="Média ponderada geral de proficiência do aluno"
    )
    total_topics_tracked: int = Field(
        description="Total de tópicos gramaticais avaliados"
    )
    mastered_topics: list[str] = Field(
        description="Lista de tópicos plenamente dominados pelo aluno"
    )
    vulnerable_topics: list[str] = Field(
        description="Tópicos que exigem reforço pedagógico prioritário"
    )
    topic_details: list[TopicProficiencyItem] = Field(
        description="Detalhamento granular por competência gramatical"
    )
    recommended_focus: str = Field(
        description="Orientação pedagógica do Magister para a próxima sessão de estudos"
    )

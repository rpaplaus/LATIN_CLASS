from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A message in the dialogue between the student and the Magister."""

    role: Literal["user", "assistant", "system"] = Field(
        description="Emissor da mensagem: 'user' (aluno) ou 'assistant' (Magister)"
    )
    content: str = Field(description="Conteúdo textual da mensagem")


class ChatInteractiveRequest(BaseModel):
    """Request payload for real-time pedagogical dialogue with Magister Latium."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Dúvida ou comentário do aluno sobre a língua latina ou história clássica",
        examples=[
            "Magister, por que os romanos diziam 'Veni, vidi, vici' com som de W?"
        ],
    )
    lesson_id: str | None = Field(
        default=None,
        description="Identificador da lição atualmente ativa para contextualização",
    )
    context_topics: list[str] = Field(
        default_factory=list,
        description="Tópicos gramaticais abordados na aula ativa",
    )


class ChatInteractiveResponse(BaseModel):
    """Response returned by Magister Latium enriched with classical knowledge."""

    reply: str = Field(
        description="Resposta humanista e instrutiva elaborada pelo Magister Latium"
    )
    sources_consulted: list[str] = Field(
        default_factory=list,
        description="Fontes consultadas (ex: 'Biblioteca de Alexandria', 'Pesquisa Arqueológica Web')",
    )
    historical_trivia_snippet: str | None = Field(
        default=None,
        description="Curiosidade histórica relevante citada na resposta",
    )

from pydantic import BaseModel, Field


class LexiconEntry(BaseModel):
    """A consolidated Latin vocabulary entry from completed lessons."""

    word: str = Field(description="Lema latino normalizado")
    dictionary_entry: str = Field(
        description="Entrada canônica de dicionário (ex: 'puella, -ae, f.')"
    )
    grammatical_class: str = Field(
        description="Classificação morfológica (ex: 'Substantivo', 'Verbo', etc.)"
    )
    translation: str = Field(description="Tradução em Português")
    example_sentence: str = Field(
        default="",
        description="Frase curta exemplificando o uso em contexto clássico",
    )
    lesson_id: str = Field(description="ID da lição de onde o vocábulo se originou")
    lesson_title: str = Field(description="Título da lição de origem")
    module_title: str = Field(description="Título do módulo de origem")
    audio_url: str = Field(description="URL de streaming do áudio MP3 em cache")
    is_favorite: bool = Field(
        default=False,
        description="Indica se o termo está salvo nos Pugillares (favoritos do aluno)",
    )


class LexiconResponse(BaseModel):
    """Aggregated lexicon response for the current student."""

    total_words: int = Field(description="Total de palavras únicas assimiladas")
    favorite_count: int = Field(description="Total de palavras salvas nos Pugillares")
    available_classes: list[str] = Field(
        default_factory=list,
        description="Lista de classes gramaticais presentes no acervo do aluno",
    )
    entries: list[LexiconEntry] = Field(
        default_factory=list,
        description="Lista consolidada de vocábulos",
    )


class FavoriteToggleRequest(BaseModel):
    """Request payload to toggle a word in Pugillares."""

    word: str = Field(description="Palavra latina a ser favoritada ou desfavoritada")


class FavoriteToggleResponse(BaseModel):
    """Response returned when toggling a vocabulary favorite."""

    word: str = Field(description="Palavra latina")
    is_favorite: bool = Field(description="Novo estado de favorito do termo")
    message: str = Field(description="Mensagem descritiva da ação realizada")

from pydantic import BaseModel, Field


class FlashcardItem(BaseModel):
    """An interactive visual and audio flashcard representing a Latin vocabulary term."""

    id: str = Field(description="Identificador único do flashcard")
    word: str = Field(description="Lema em Latim clássico")
    dictionary_entry: str = Field(
        description="Entrada lexicográfica (ex: 'gladius, -i, m.')"
    )
    grammatical_class: str = Field(description="Classificação morfológica")
    translation: str = Field(description="Significado e tradução em Português")
    example_sentence: str = Field(description="Frase de exemplo em latim clássico")
    image_url: str | None = Field(
        default=None, description="URL da ilustração temática romana"
    )
    audio_url: str | None = Field(
        default=None, description="URL do arquivo de pronúncia clássica em áudio"
    )
    audio_base64: str | None = Field(
        default=None, description="Buffer base64 para reprodução inline imediata"
    )


class LessonFlashcardsResponse(BaseModel):
    """Response containing full deck of visual/audio flashcards for a Latin lesson."""

    lesson_id: str = Field(description="ID da lição associada")
    lesson_title: str = Field(description="Título da lição")
    total_cards: int = Field(description="Quantidade total de cartões no deck")
    flashcards: list[FlashcardItem] = Field(
        description="Coleção de flashcards do vocabulário"
    )

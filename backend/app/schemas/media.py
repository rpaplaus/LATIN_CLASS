from pydantic import BaseModel, Field


class TTSRequest(BaseModel):
    """Payload for Latin text pronunciation request."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Palavra ou frase em Latim a ser pronunciada",
        examples=["Gallia est omnis divisa in partes tres", "puella cantat"],
    )
    voice: str = Field(
        default="onyx",
        description="Voz clássica: 'onyx' (grave/solene), 'alloy' (neutro), 'fable' ou 'nova'",
    )


class TTSResponse(BaseModel):
    """Metadata and links for generated or cached Latin audio pronunciation."""

    audio_hash: str = Field(
        description="Hash SHA-256 do texto e voz para identificação única"
    )
    audio_url: str = Field(description="URL para streaming direto do arquivo MP3")
    audio_base64: str = Field(
        description="Buffer de áudio codificado em base64 para reprodução instantânea"
    )
    cached: bool = Field(
        description="Indica se o áudio foi servido do cache (Redis ou disco)"
    )
    text: str = Field(description="Texto original normalizado")
    voice: str = Field(description="Voz selecionada")

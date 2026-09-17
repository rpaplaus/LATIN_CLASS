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
    mime_type: str = Field(
        default="audio/mpeg",
        description="MIME type do áudio gerado (audio/mpeg ou audio/wav)",
    )


class WordPhoneticBreakdown(BaseModel):
    """Evaluation breakdown for an individual Latin word in student speech."""

    word: str = Field(description="Palavra alvo em latim")
    status: str = Field(
        description="Avaliação de acurácia: 'correct', 'acceptable' ou 'needs_practice'"
    )
    accuracy: float = Field(
        ge=0.0,
        le=1.0,
        description="Índice de similaridade fonética (0.0 a 1.0)",
    )
    phonetic_rule_note: str | None = Field(
        default=None,
        description="Observação fonética sobre desinência ou regra canônica",
    )


class PronunciationEvaluationResponse(BaseModel):
    """Complete multimodal phonetic pronunciation evaluation result."""

    target_text: str = Field(
        description="Texto clássico alvo que o aluno deveria pronunciar"
    )
    transcribed_text: str = Field(
        description="Transcrição fonética capturada pelo motor STT"
    )
    overall_score: int = Field(
        ge=0,
        le=100,
        description="Nota geral de fidelidade clássica (0 a 100)",
    )
    is_passing: bool = Field(
        description="Indica se a pronúncia atingiu o padrão mínimo (score >= 70)"
    )
    word_breakdown: list[WordPhoneticBreakdown] = Field(
        description="Análise palavra por palavra da pronúncia"
    )
    phonetic_tips: str = Field(
        description="Conselho do Magister sobre regras da Pronuntiatio Restituta aprimoradas ou a revisar"
    )
    critical_phonemes_detected: dict[str, bool] = Field(
        default_factory=dict,
        description="Detecção de fonemas críticos clássicos (ex: 'restored_v_as_w', 'velar_c', 'diphthong_ae')",
    )

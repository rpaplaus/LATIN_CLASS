# 🏛️ Latin Class — Plano de Implementação da Fase 6: O Senado Romano (Imersão e Gamificação)

> **Documento de Arquitetura e Engenharia**  
> **Status:** Proposta de Planejamento (Aguardando Aprovação do Tech Lead)  
> **Alvo:** Latium AI — Backend (FastAPI, Redis, PostgreSQL/SQLAlchemy, LangGraph) & Frontend (React/TypeScript)

---

## 1. Visão Geral da Fase 6

A **Fase 6: O Senado Romano** transforma o Latium AI de uma ferramenta de aprendizado textual em uma experiência imersiva e gamificada:
1. **Pronúncia Clássica (TTS):** Geração de pronúncia em áudio clássico para palavras e frases em latim, com cache em Redis e disco local, permitindo streaming rápido e suporte nativo ao Safari/iOS.
2. **Flashcards Visuais com Agente Ilustrador:** Geração de cartões de vocabulário com arte temática clássica (mosaicos, esculturas e pinturas romanas) via `ModelRole.ILLUSTRATOR` e reprodução de áudio.
3. **Gamificação e Badges do Senado:** Sistema de títulos e comendas da Roma Antiga (*Tiro*, *Centurio*, *Censor Severus*, *Senator*, *Legatus Legionis*), desbloqueados por ofensiva diária (*streak*), notas de excelência e avanço modular.

---

## 2. Geração, Cache e Distribuição de Áudio (Text-to-Speech)

### 2.1. Arquitetura do Mecanismo de TTS
Para reproduzir com autenticidade a pronúncia clássica do latim (*pronuntiatio restituta*):
- **Provedor Principal:** OpenAI TTS (`model="tts-1"`, voz `"onyx"` ou `"alloy"`). A voz `onyx` possui timbre barítono grave e solene, ideal para a oratória e o latim clássico.
- **Resiliência e Fallback Offline:**
  - Gerador determinístico de áudio sintético / buffer MP3 estático em caso de ausência de chaves de API nos testes ou falha de conectividade.
  - O endpoint suporta entrega tanto como arquivo binário (`audio/mpeg`) quanto como `data:audio/mpeg;base64,...` para reprodução instantânea no iOS sem requisições HTTP adicionais.

### 2.2. Estratégia de Cache em Dois Níveis (Redis + Disco)
Como a pronúncia do vocabulário canônico latino é imutável, o áudio gerado deve ser salvo permanentemente em cache:
1. **Chave Canônica de Hash:**
   $$\text{audio\_hash} = \text{SHA256}(\text{normalized\_text} + \text{":"} + \text{voice})$$
2. **Nível 1 — Redis Cache (Memória Ultrarrápida):**
   - Chave: `latin_tts:audio:{audio_hash}`.
   - Valor: buffer binário MP3 ou string Base64.
   - TTL: 30 dias com renovação em acesso frequente.
3. **Nível 2 — Cache Local em Disco (Storage Persistente):**
   - Diretório montado: `backend/storage/audio/{audio_hash}.mp3` (volume mapeado no Docker).
   - Se o Redis reiniciar, o arquivo persiste em disco e é reaquecido no Redis transparentemente.

### 2.3. Endpoints da API de Áudio
- **`POST /api/v1/media/tts`**
  - Payload: `{"text": "Gallia est omnis divisa in partes tres", "voice": "onyx"}`
  - Resposta:
    ```json
    {
      "audio_hash": "a1b2c3d4...",
      "audio_url": "/api/v1/media/audio/a1b2c3d4...",
      "audio_base64": "SUQzBAAAAAAAI1RTU0U...",
      "cached": true,
      "text": "Gallia est omnis divisa in partes tres"
    }
    ```
- **`GET /api/v1/media/audio/{audio_hash}`**
  - Retorna `Response(content=audio_bytes, media_type="audio/mpeg")` com headers HTTP de cache agressivo:
    - `Cache-Control: public, max-age=2592000, immutable`
    - Suporte a `Accept-Ranges: bytes` para streaming nativo no Safari iOS.

---

## 3. Fluxo de Geração das Imagens para os Flashcards

### 3.1. O Agente Ilustrador (*Pictor Latium*)
No [`backend/app/agent/llm_factory.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/agent/llm_factory.py), expandimos `ModelRole` com a nova função:
```python
class ModelRole(StrEnum):
    ROUTER = "router"
    TUTOR = "tutor"
    EVALUATOR = "evaluator"
    ILLUSTRATOR = "illustrator"  # Novo
```

### 3.2. Pipeline de Prompt e Geração Visual
1. **Entrada do Vocabulário:**
   - Palavra em latim: *gladius*
   - Tradução: *espada curta romana*
   - Contexto: *arma praecipua legionarii romani*
2. **Expansão de Prompt pelo Ilustrador:**
   - O agente gera um prompt estilizado:
     > *"An authentic classical Roman gladius short sword resting on a weathered marble pedestal in a Roman legionary camp, warm golden Mediterranean sunlight, oil painting museum aesthetic, highly detailed antiquity art style."*
3. **Execução Multi-Provedor com Fallback:**
   - **Provedor 1 (DALL-E 3 / OpenAI):** Geração via API de imagens em resolução 1024x1024.
   - **Provedor 2 (Gemini / Imagen 3):** Geração via Google GenAI.
   - **Fallback Deterministico:** SVG/Canvas gerado proceduralmente com moldura clássica dourada, medalhão de louros e o lema latino impresso, garantindo 100% de funcionamento mesmo sem credenciais de API.
4. **Cache e Associação:**
   - A imagem gerada é salva em `backend/storage/images/{image_hash}.webp` e servida via endpoint estático ou CDN.

### 3.3. Endpoint de Flashcards de Lição
- **`GET /api/v1/lessons/{lesson_id}/flashcards`**
  - Retorna a lista de flashcards com áudio e ilustração integrados:
    ```json
    [
      {
        "id": "flashcard-1",
        "word": "gladius",
        "dictionary_entry": "gladius, -i, m.",
        "grammatical_class": "Substantivo masculino de 2ª declinação",
        "translation": "espada curta",
        "example_sentence": "Miles gladium stringit.",
        "image_url": "/api/v1/media/images/gladius_hash.webp",
        "audio_url": "/api/v1/media/audio/gladius_audio_hash"
      }
    ]
    ```

---

## 4. Modelagem de Dados dos Badges no SQLAlchemy

### 4.1. Novas Tabelas: `badges` e `user_badges`

```python
import uuid
from datetime import UTC, datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.user import User


class Badge(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Canonic roman honor, rank or achievement that students can earn."""

    __tablename__ = "badges"

    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    latin_motto: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    icon_name: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)  # streak, score, completion, special
    tier: Mapped[str] = mapped_column(String(32), default="bronze", nullable=False)  # bronze, silver, gold, laurel
    requirement_type: Mapped[str] = mapped_column(String(64), nullable=False)
    requirement_value: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    xp_reward: Mapped[int] = mapped_column(Integer, default=50, nullable=False)

    user_badges: Mapped[list["UserBadge"]] = relationship("UserBadge", back_populates="badge", cascade="all, delete-orphan")


class UserBadge(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Association table recording when a student unlocked an honor badge."""

    __tablename__ = "user_badges"
    __table_args__ = (
        UniqueConstraint("user_id", "badge_id", name="uq_user_badge"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    badge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("badges.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    unlocked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    metadata_: Mapped[dict[str, object]] = mapped_column("metadata", JSONB, default=dict, nullable=False)

    user: Mapped["User"] = relationship("User")
    badge: Mapped["Badge"] = relationship("Badge", back_populates="user_badges")
```

### 4.2. Catálogo Canônico de Conquistas (*Cursus Honorum*)

| Código | Título | Lema Latino | Categoria | Regra de Desbloqueio |
|---|---|---|---|---|
| `TIRO_PRIMUS` | **Tiro Primus** | *Initium sapientiae* | `completion` | Concluir a primeira lição. |
| `CENTURIO_STREAK_3` | **Centurio Fideli** | *Virtus in constantia* | `streak` | Ofensiva de 3 dias consecutivos. |
| `LEGATUS_STREAK_7` | **Legatus Legionis** | *Nulla dies sine linea* | `streak` | Ofensiva de 7 dias consecutivos. |
| `CENSOR_SEVERUS` | **Censor Severus** | *Summa cum laude* | `score` | Tirar nota 100 em avaliação do Censor Latium. |
| `SENATOR_MODULE_1` | **Senator Romanus** | *Ad astra per aspera* | `completion` | Concluir 100% das lições do Módulo I. |
| `BIBLIOTHECA_ALEXANDRIA` | **Scriba Bibliothecae** | *Ex libris lux* | `special` | Consultar citações clássicas da biblioteca. |
| `IMPERATOR_PONTIFEX` | **Imperator Latium** | *Veni, vidi, vici* | `score` | Acumular 1000 pontos totais de aprendizado. |

### 4.3. Motor de Avaliação de Conquistas (`app/services/gamification.py`)
- Invocado automaticamente após:
  - `POST /api/v1/lessons/{lesson_id}/complete`
  - `POST /api/v1/lessons/{lesson_id}/evaluate`
- Avalia os critérios e retorna na resposta da requisição os `newly_unlocked_badges: list[BadgeRead]`. O frontend pode acionar animações visuais com confetes e medalhões imperiais!

---

## 5. Atualização do Frontend (React + TypeScript)

1. **Componente de Pronúncia (`LatinAudioButton`):**
   - Botão discreto com ícone de alto-falante (`Volume2`) ao lado de palavras em latim nas lições e no vocabulário.
   - Cache no navegador via `AudioContext` / `<audio>` com controle de estado (tocando, carregando, erro).
2. **Deck de Flashcards Interativos (`FlashcardDeck` / `FlashcardModal`):**
   - Flip 3D suave com CSS (frente: imagem clássica + palavra em latim + botão de pronúncia; verso: tradução, classe morfológica e exemplo).
3. **Senado Romano & Mural de Conquistas (`BadgesModal` / `SenateHall`):**
   - Exibição da galeria de medalhões dourados e de louros.
   - Badges bloqueados exibidos em tom sombrio (escultura em relevo de pedra), e badges conquistados com brilho dourado e lema latino em evidência.
4. **Atualização do `ProgressContext`:**
   - Adicionados `badges: UserBadge[]`, `unlockedBadgeModal: Badge | null`.
   - Pop-up automático de celebração quando uma lição desbloqueia uma nova comenda.

---

## 6. Plano de Migração e Testes

1. **Migração de Banco de Dados:**
   - `0004_roman_senate_badges.py`: Criação das tabelas `badges` e `user_badges` com índices e foreign keys.
   - Seed automático dos 7 badges canônicos do *Cursus Honorum*.
2. **Suíte de Testes:**
   - `tests/test_media_tts.py`: Testes unitários de hashing, fallback de áudio e cache em Redis.
   - `tests/test_illustrator.py`: Geração de flashcards e resolução de imagens.
   - `tests/test_gamification.py`: Desbloqueio de badges por streak, nota e conclusão de módulo sem duplicações.
   - Verificação rigorosa: Pytest, Mypy Strict e Ruff.

---

> 🛑 **SYSTEM HALT RESPEITADO:** Nenhuma alteração no código-fonte foi realizada. Aguardo as diretrizes e a aprovação do Tech Lead para iniciar a execução!

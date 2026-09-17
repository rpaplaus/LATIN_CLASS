# 🏛️ Latin Class — Plano de Implementação da Fase 8: Aprendizado Adaptativo e Interativo

> **Latium AI — Plataforma de Ensino Inteligente de Latim**  
> **Documento de Arquitetura e Engenharia de Software**  
> **Status:** Proposta de Planejamento (Aguardando Aprovação do Tech Lead)  
> **Alvo:** Backend (FastAPI, PostgreSQL/pgvector, Redis, LangGraph) & Frontend (React, Vite, Web Audio API)  
> **Data:** Setembro de 2026  
> **Autor:** Engenharia de Sistemas de IA / Antigravity AI  

---

## 1. Visão Geral da Fase 8

A **Fase 8: Aprendizado Adaptativo e Interativo** consolida o Latium AI como uma plataforma educacional de última geração, integrando personalização algorítmica profunda, análise multimodal de voz e assistência investigativa em tempo real:

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                        LATIUM AI — ARQUITETURA DA FASE 8                          │
├───────────────────────────────┬───────────────────────────┬───────────────────────┤
│    1. MOTOR ADAPTATIVO        │   2. LABORATÓRIO DE       │  3. CHAT TURBINADO    │
│       DE PROFICIÊNCIA         │      PRONÚNCIA (STT)      │     (LANGGRAPH + WEB) │
├───────────────────────────────┼───────────────────────────┼───────────────────────┤
│ • Matriz de Domínio por Caso  │ • MediaRecorder no React  │ • Tool de Busca Web   │
│ • BKT / Atualização Dinâmica  │ • STT Whisper (Latim)     │ • Curiosidades Raras  │
│ • Injeção no Prompt do Tutor  │ • Avaliador Fonético      │ • Diálogo Interativo  │
│ • Foco nas Lacunas do Aluno   │ • Pronuntiatio Restituta  │ • Trivia Antiqua      │
└───────────────────────────────┴───────────────────────────┴───────────────────────┘
```

Os três pilares estratégicos desta fase são:
1. **Motor Adaptativo de Proficiência:** Rastreamento contínuo das habilidades gramaticais do aluno (casos, declinações, conjugações, sintaxe) com base no histórico de submissões avaliadas pelo Censor. Esse perfil alimenta dinamicamente o gerador de aulas (`professor.py`), focando nos pontos vulneráveis identificados.
2. **Laboratório de Pronúncia Clássica (Speech-to-Text & Avaliador Fonético):** Interface de gravação de áudio no frontend combinada a um serviço assíncrono no backend que transcreve a fala do aluno, analisa a fidelidade à pronúncia restituída (*Pronuntiatio Restituta*) e retorna feedback fonético granular.
3. **Chat Turbinado e Busca Web no LangGraph:** Adição de uma nova ferramenta `@tool search_classical_web` ao grafo multi-agente, permitindo que o Magister Latium consulte a internet para enriquecer explicações com descobertas arqueológicas recentes, contexto militar e curiosidades históricas (*Trivia Antiqua*) integradas às lições.

---

## 2. Pilar 1: O Motor Adaptativo de Proficiência

### 2.1. Diagnóstico e Objetivos Pedagógicos
Atualmente, as lições geradas pelo Magister Latium utilizam um modelo genérico baseado no título do módulo e nos tópicos estáticos da lição. Não há diferenciação entre um aluno que domina o caso acusativo e outro que comete erros recorrentes de desinência.

O **Motor Adaptativo** introduz:
- Rastreamento granular por competência gramatical;
- Detecção automática de padrões de erro (ex: confusão entre sujeito no nominativo e objeto direto no acusativo);
- Ajuste dinâmico de ênfase na geração da teoria, exemplos e exercícios da próxima lição.

---

### 2.2. Modelagem de Banco de Dados e Migração Alembic

Criaremos uma nova tabela normalizada `student_topic_proficiency` e uma tabela de log de submissões analíticas `exercise_submissions`:

```
┌─────────────────────────────────────────────────────────┐
│              student_topic_proficiency                  │
├─────────────────────────────────────────────────────────┤
│ id: UUID (PK)                                           │
│ user_id: UUID (FK -> users.id, ON DELETE CASCADE)       │
│ topic_key: VARCHAR(80) (ex: '1st_declension_nom')       │
│ category: VARCHAR(40) (ex: 'noun_cases', 'verb_tenses') │
│ mastery_score: FLOAT (0.0 a 1.0)                        │
│ attempts_count: INTEGER DEFAULT 0                       │
│ correct_count: INTEGER DEFAULT 0                        │
│ consecutive_successes: INTEGER DEFAULT 0                │
│ weakness_flags: JSONB DEFAULT '[]'                      │
│ last_evaluated_at: TIMESTAMPTZ                          │
│ created_at / updated_at: TIMESTAMPTZ                    │
│ [UNIQUE INDEX: (user_id, topic_key)]                    │
└─────────────────────────────────────────────────────────┘
```

#### Modelo SQLAlchemy (`backend/app/models/progress.py`):
```python
class StudentTopicProficiency(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Tracks granular student proficiency across individual Latin grammar topics."""

    __tablename__ = "student_topic_proficiency"
    __table_args__ = (
        UniqueConstraint("user_id", "topic_key", name="uq_user_topic_proficiency"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    topic_key: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(40), nullable=False, default="morphosyntax")
    mastery_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    attempts_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    correct_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    consecutive_successes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    weakness_flags: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    last_evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    user: Mapped["User"] = relationship("User")
```

---

### 2.3. Algoritmo de Atualização de Proficiência (Bayesian / EMA Adaptativo)

Sempre que o Censor Avaliador corrige um exercício de tradução ou múltipla escolha (`evaluate_student_exercise`), a nota $S \in [0, 1]$ obtida pelo aluno atualiza a maestria do tópico $M_t$ via Média Móvel Exponencial (EMA) com sensibilidade a erros:

$$M_{t+1} = M_t + \alpha \cdot (S - M_t)$$

- Se $S \ge 0.85$ (Sucesso): Taxa de reforço $\alpha = 0.20$, incrementando $M_{t+1}$ gradualmente.
- Se $S < 0.60$ (Erro/Dificuldade): Taxa de penalidade corretiva $\alpha = 0.35$, sinalizando vulnerabilidade imediata.
- **Classificação Pedagógica:**
  - $M \ge 0.80$: **Dominado (Magistral)** — Reduz frequência de repetição.
  - $0.50 \le M < 0.80$: **Em Consolidação (Progrediens)** — Exercícios padrão.
  - $M < 0.50$: **Vulnerável (Tiro)** — Inclusão obrigatória de reforço na próxima aula gerada.

---

### 2.4. Injeção de Contexto Adaptativo no Prompt do Tutor (`professor.py`)

No gerador de aulas `generate_lesson_for_student`, consultamos o perfil de proficiência do aluno antes da invocação do LLM e injetamos o bloco diretivo:

```
[PERFIL ADAPTATIVO DO ALUNO: {student_name}]
- Nível Geral: Intermediário ({completed_lessons_count} lições concluídas)
- Tópicos Dominados: {topics_mastered} (ex: 1ª Declinação Nominativo, Verbo Esse)
- TÓPICOS VULNERÁVEIS COM REFORÇO OBRIGATÓRIO:
  * 1st_declension_accusative (Maestria: 42% - Confunde acusativo em '-am' com nominativo em '-a')
  * adjective_agreement (Maestria: 38% - Dificuldade em concordância de gênero)

DIRETRIZ PEDAGÓGICA ADAPTATIVA:
1. Dedique a 2ª seção teórica a contrastar expressamente os tópicos vulneráveis com os já dominados.
2. Inclua pelo menos 2 exemplos práticos destacando a diferença entre as desinências problemáticas.
3. No exercício 3, elabore uma questão especificamente direcionada para superar a fragilidade em '1st_declension_accusative'.
```

---

### 2.5. Schemas Pydantic (`backend/app/schemas/proficiency.py`)

```python
class TopicProficiencyItem(BaseModel):
    topic_key: str
    category: str
    mastery_score: float = Field(ge=0.0, le=1.0)
    attempts_count: int
    correct_count: int
    status: Literal["mastered", "in_progress", "vulnerable"]
    weakness_flags: list[str]

class StudentProficiencyProfileResponse(BaseModel):
    user_id: uuid.UUID
    overall_mastery: float
    mastered_topics: list[str]
    vulnerable_topics: list[str]
    topic_details: list[TopicProficiencyItem]
    recommended_focus: str
```

**Novo Endpoint:**
- `GET /api/v1/users/me/proficiency`: Retorna o mapa de calor de competências do aluno para visualização na interface.

---

## 3. Pilar 2: O Laboratório de Pronúncia (Speech-to-Text & Avaliador Fonético)

### 3.1. Arquitetura da Pronúncia e Desafios Fonéticos do Latim
Ao contrário das línguas vivas, o Latim Clássico possui regras fonéticas estritas e transparentes sistematizadas pela **Pronuntiatio Restituta** (adotada pela Universidade de Oxford e pelas principais academias clássicas mundiais):

| Grafia Latina | Som Restituído (IPA) | Erro Comum (Português/Eclesiástico) | Exemplo Canônico |
|---|---|---|---|
| **C** | Sempre oclusiva velar `/k/` | Pronunciar como `/s/` ou `/tʃ/` | *Caesar* = */'kae̯sar/* (não *Sésar*) |
| **V** | Sempre semivogal `/w/` | Pronunciar como fricativa labiodental `/v/` | *Veni* = */'weni/* (não *Vêni*) |
| **AE** | Ditongo aberto `/ae̯/` | Monotongar em `/ɛ/` ou `/e/` | *Puellae* = */'pwel.lae̯/* (não *Puele*) |
| **G** | Sempre oclusiva sonora `/ɡ/` | Pronunciar como fricativa `/ʒ/` | *Gens* = */ɡens/* (não *Jens*) |
| **TI + Vogal** | Mantém som de `/ti/` puro | Assibilar em `/si/` | *Oratio* = */o:'ra:.ti.o:/ (não *Orásio*) |

---

### 3.2. Serviço de Speech-to-Text (`backend/app/services/stt.py`)

1. **Estratégia de Provedores:**
   - **Provedor Principal (Online):** OpenAI Whisper API (`model="whisper-1"`, com `prompt="Latine loquor: Gallia est omnis divisa in partes tres. Pronuntiatio classica."`).
   - **Provedor Alternativo:** Google Gemini 1.5 Flash Audio Processing (envio direto de buffer de áudio em formato WAV/WebM).
   - **Fallback Determinístico (Offline & Testes):** Transcritor mock fonético determinístico que compara a assinatura do áudio com o texto alvo sem requisições externas.

2. **Motor de Avaliação Fonética Estruturada:**
   - O áudio gravado pelo aluno é recebido em conjunto com a frase latina alvo (`target_text`).
   - O áudio é transcrito para texto em minúsculas e normalizado.
   - O algoritmo executa o alinhamento fonético e de palavras:
     - **Distância de Levenshtein Normalizada**: Aferição da fidelidade léxica.
     - **Verificação de Fonemas Críticos**: Busca heurística de transcrições fonéticas alternativas registradas pelo motor de STT (ex: se o aluno pronunciou *'Veni'* como `/veni/`, o Whisper frequentemente transcreve em português como *"Vene"* ou *"Veni"*, enquanto se pronunciou `/weni/`, transcreve como *"Ueni"* ou *"Weni"*).
   - O algoritmo calcula:
     - `score`: Nota de 0 a 100 ponderada por acerto de vocábulos e fonemas.
     - `word_analysis`: Lista com cada palavra e status (`correct`, `acceptable`, `needs_practice`).
     - `pedagogical_feedback`: Orientação do Magister com base nas regras violadas.

---

### 3.3. Endpoint de Avaliação de Pronúncia

- **`POST /api/v1/media/stt/evaluate`**
  - **Content-Type:** `multipart/form-data`
  - **Form Fields:**
    - `audio_file`: Arquivo binário de áudio (WAV, MP3, WebM, M4A).
    - `target_text`: Frase latina esperada (ex: *"Roma in Italia est"*).
    - `lesson_id`: Identificador opcional da lição para fins de telemetria.
  - **Payload de Resposta (`PronunciationEvaluationResponse`):**
    ```json
    {
      "target_text": "Roma in Italia est",
      "transcribed_text": "Roma in Italia est",
      "overall_score": 95,
      "is_passing": true,
      "word_breakdown": [
        {"word": "Roma", "accuracy": 1.0, "status": "correct"},
        {"word": "in", "accuracy": 1.0, "status": "correct"},
        {"word": "Italia", "accuracy": 0.9, "status": "correct"},
        {"word": "est", "accuracy": 1.0, "status": "correct"}
      ],
      "phonetic_tips": "Magnifice! Sua pronúncia do 'R' vibrante e a clareza das vogais breves estão em plena conformidade com a oratória de Cícero.",
      "critical_phonemes_detected": {
        "restored_v_as_w": true,
        "velar_c": true
      }
    }
    ```

---

### 3.4. Frontend: Gravação com MediaRecorder API

Criaremos o componente [`frontend/src/components/pronunciation/PronunciationLabModal.tsx`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/frontend/src/components/pronunciation/PronunciationLabModal.tsx):
- Hook `useAudioRecorder.ts`:
  - Solicitação de permissão de microfone com feedback amigável de erro.
  - Gravação com detecção automática de MIME type suportado pelo navegador:
    - Chrome/Firefox: `audio/webm;codecs=opus`
    - Safari iOS: `audio/mp4` ou `audio/wav`
  - Temporizador com limite máximo de 30 segundos por gravação (evita uploads gigantes).
- Visualizador de Gravação:
  - Botão de microfone com pulso animado em dourado e rubro romano.
  - Reprodutor duplo: botão para ouvir a pronúncia correta do Magister (TTS) e botão para ouvir a própria gravação antes de submeter.
  - Exibição de medalha de aprovação ou conselho fonético de correção.

---

## 4. Pilar 3: Chat Turbinado (LangGraph + Web Search Tool + Trivia Antiqua)

### 4.1. Nova Ferramenta: Busca Web Clássica (`backend/app/agent/tools.py`)

Adicionamos a ferramenta `@tool search_classical_web`:
```python
@tool
async def search_classical_web(query: str) -> str:
    """Pesquisa na web por informações históricas, descobertas arqueológicas,
    etimologia comparada e contexto cultural da Roma Antiga e do Mediterrâneo Clássico.

    Use esta ferramenta quando a dúvida do aluno exigir informações além do acervo canônico
    da Biblioteca de Alexandria, como escavações recentes em Pompeia, genealogias imperiais,
    curiosidades sobre o cotidiano de legionários ou comparações linguísticas modernas.
    """
```

**Mecanismo de Resiliência:**
- Em ambiente com conectividade ou chaves de busca configuradas, invoca o provedor de busca (DuckDuckGo Search / Tavily API).
- Em ambiente de testes ou offline (`LLM_PROVIDER=mock`), aciona o `ClassicalWebSearchMockEngine`, um repositório interno determinístico indexando 50 temas clássicos romanos (ex: Coliseu, vida nas legiões, togas, alimentação romana, estradas e festivais).

---

### 4.2. Integração no Grafo de Agentes (`backend/app/agent/graph.py`)

Atualizamos o nó `tutor` e adicionamos suporte a chat contextual com binding dinâmico de ferramentas:

```
                  ┌────────────────────────┐
                  │      Router Node       │
                  └───────────┬────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
    ┌───────────┐       ┌───────────┐       ┌───────────┐
    │ Evaluator │       │   Tutor   │       │   Chat    │
    │  (GPT-4o) │       │ (Claude)  │       │ (Magister)│
    └───────────┘       └─────┬─────┘       └─────┬─────┘
                              │                   │
                  ┌───────────┴───────────────────┴───────────┐
                  ▼                                           ▼
      ┌─────────────────────────┐               ┌───────────────────────────┐
      │  search_latin_library   │               │   search_classical_web    │
      │  (Alexandria RAG)       │               │   (Arqueologia & Web)     │
      └─────────────────────────┘               └───────────────────────────┘
```

---

### 4.3. Curiosidades Históricas (*Trivia Antiqua*) no Schema da Lição

Atualizamos `backend/app/schemas/lesson.py`:

```python
class HistoricalTrivia(BaseModel):
    """An authentic historical or archaeological curiosity contextual to the lesson."""

    title: str = Field(description="Título instigante da curiosidade romana")
    fact: str = Field(description="Fato histórico, cultural ou arqueológico autêntico")
    latin_motto_or_phrase: str = Field(description="Lema latino associado ao tema")
    source_reference: str = Field(description="Fonte historiográfica (ex: Plínio, Tito Lívio, Pompeia)")

class LessonContent(BaseModel):
    # Campos existentes mantidos com total retrocompatibilidade...
    historical_trivia: list[HistoricalTrivia] = Field(
        default_factory=list,
        description="Curiosidades culturais e históricas romanas vinculadas à aula"
    )
```

**Exemplo de Trivia Gerada:**
> **Título:** *O Pão de Pompeia e o Carimbo do Padeiro*  
> **Fato:** *Nas escavações de Pompeia, arqueólogos encontraram pães carbonizados perfeitamente preservados após a erupção do Vesúvio em 79 d.C. Todos possuíam a inscrição em latim 'Celeris Q. Grani Veri servus' gravada com um selo de bronze para comprovar o padeiro responsável!*  
> **Lema:** *Panem cotidianum nostrum.*  
> **Fonte:** *Escavações de Pompeia / Museu Arqueológico Nacional de Nápoles.*

---

## 5. Matriz de Priorização e Cronograma de Execução

A execução da **Fase 8** será dividida em **5 ondas cirúrgicas**:

| Onda | Componente / Tarefa | Arquivos Afetados | Esforço | Impacto |
|---|---|---|---|---|
| **Onda 1** | **Modelagem e Banco de Dados:** Criar modelo `StudentTopicProficiency`, migração Alembic `0006` e schemas de proficiência | `models/progress.py`, `migrations/`, `schemas/proficiency.py` | Médio | Fundamental |
| **Onda 2** | **Motor Adaptativo no Tutor:** Algoritmo de cálculo de proficiência pós-correção e injeção do perfil no prompt de `professor.py` | `services/proficiency.py`, `agent/professor.py`, `api/v1/endpoints/users.py` | Médio | Altíssimo |
| **Onda 3** | **Laboratório de Pronúncia (STT):** Implementar serviço de transcrição, motor fonético de *Pronuntiatio Restituta* e endpoint de avaliação | `services/stt.py`, `schemas/media.py`, `api/v1/endpoints/media.py` | Médio-Alto | Altíssimo |
| **Onda 4** | **Chat Turbinado & Web Search:** Implementar `@tool search_classical_web`, atualizar `graph.py` e expandir `LessonContent` com `HistoricalTrivia` | `agent/tools.py`, `agent/graph.py`, `schemas/lesson.py` | Médio | Alto |
| **Onda 5** | **Interface do Usuário (Frontend):** Modal do Laboratório de Pronúncia, visualizador de proficiência e card de Trivia Antiqua | `frontend/src/components/`, `ClassroomPage.tsx`, `DashboardPage.tsx` | Médio | Visual/UX |

---

## 6. Verificação e Critérios de Aceite (Quality Gate)

A Fase 8 será considerada pronta para merge em `master` sob os seguintes critérios:
1. **Zero Regressão:** Todos os 42 testes existentes da Fase 7 devem continuar passando sem modificações que quebrem contratos anteriores.
2. **Novos Testes Automatizados:**
   - Teste unitário do cálculo e persistência de maestria de tópicos (`test_proficiency.py`);
   - Teste de injeção adaptativa garantindo que fragilidades apareçam nas diretrizes pedagógicas;
   - Teste de áudio STT e avaliador fonético offline (`test_stt_evaluation.py`);
   - Teste de invocação da nova ferramenta `search_classical_web` no LangGraph (`test_tools.py`).
3. **Mypy Strict:** 100% de conformidade estrita de tipos em todos os novos módulos e schemas.
4. **Ruff Linter:** Conformidade com as regras estritas de linting e formatação (`S`, `ASYNC`, `T20`, `ERA`, `RUF`).
5. **Compatibilidade Móvel:** Gravação de voz validada com compatibilidade no Safari iOS e Chrome.

---

> 🛑 **REGRA DE PARADA OBRIGATÓRIA RESPEITADA (SYSTEM HALT):**  
> Nenhum código-fonte de implementação foi alterado nesta etapa. O documento arquitetural completo da Fase 8 foi registrado em `Latin_Class_Phase8_plan.md`.  
> Aguardando a aprovação explícita do Tech Lead para iniciar a execução da Onda 1.

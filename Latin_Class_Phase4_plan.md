# Plano da Fase 4: Avaliador e Multi-Modelo (Latium AI)

**Documento de Planejamento de Engenharia e Arquitetura**  
**Versão:** 1.0  
**Status:** Aguardando Aprovação (Tech Lead Review)  

---

## 1. Visão Geral e Objetivos da Fase 4

Na Fase 2 e 3, construímos o motor base do Latium AI, a persistência de progresso no PostgreSQL com sessões longas no Redis, o Agente Professor inicial e a interface web mobile-first em React.

O objetivo da **Fase 4** é elevar a inteligência do sistema a um patamar de tutoria socrática avançada:
1. **Multi-Model Orchestration:** Desacoplar a geração de IA para utilizar o modelo mais eficiente em cada etapa:
   - **Groq (Llama 3.1):** Roteador ultra-rápido de baixa latência para classificação de intenção e seleção de fluxo.
   - **Anthropic (Claude 3.5 Sonnet):** Geração humanista e rica em nuances filológicas das aulas (*Magister Latium*).
   - **OpenAI (GPT-4o):** Correção morfológica rigorosa, sintaxe analítica e atribuição de nota das respostas abertas (*Agente Avaliador / Censor*).
2. **Agente Avaliador (Censor Latium):** Um novo agente especializado em correção gramatical de respostas livres (traduções e composições em latim), retornando análises morfológicas detalhadas por palavra e sugestões de estilo clássico.
3. **Interface React Enriquecida:** Atualizar a Sala de Aula para exibir cartões de feedback gramatical interativos, com análise de casos, tempos verbais, concordâncias e alternativas estilísticas de Cícero/César.

---

## 2. Reestruturação do LangGraph e Multi-Modelo

### 2.1. Arquitetura do Modelo Multi-Provider

```
                           [ Requisição do Aluno ]
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │   Roteador Rápido (Groq)  │
                        │   Llama 3.1 70B / 8B      │
                        └─────────────┬─────────────┘
                                      │
            ┌─────────────────────────┴─────────────────────────┐
            │                                                   │
  [ Gerar Nova Aula ]                                [ Corrigir Exercício ]
            │                                                   │
            ▼                                                   ▼
┌───────────────────────────┐                       ┌───────────────────────────┐
│   Magister Latium (Claude)│                       │   Agente Avaliador (GPT)  │
│   Claude 3.5 Sonnet /     │                       │   GPT-4o / GPT-4o-mini    │
│   Haiku (Anthropic)       │                       │   (OpenAI)                │
└───────────────────────────┘                       └───────────────────────────┘
```

### 2.2. Fábrica de LLMs (`backend/app/agent/llm_factory.py`)

Para manter conformidade com os princípios SOLID e evitar acoplamento rígido a um único fornecedor, criaremos um módulo centralizado de instanciacão de LLMs com fallbacks elegantes:

```python
# backend/app/agent/llm_factory.py

from enum import Enum
from typing import Any
from app.core.config import settings

class ModelRole(str, Enum):
    ROUTER = "router"          # Groq (baixa latência)
    LESSON_TUTOR = "tutor"     # Claude 3.5 Sonnet (pedagogia e estilo humanista)
    EVALUATOR = "evaluator"    # GPT-4o (precisão lógica e sintática)

def get_llm_for_role(role: ModelRole) -> Any:
    """
    Retorna o cliente LLM apropriado com base na função e nas credenciais configuradas.
    Se a chave de um provedor de ponta não estiver disponível, faz fallback automático:
      1. Claude -> Gemini 1.5 Pro -> OpenAI -> Mock
      2. GPT-4o -> Claude -> Gemini -> Mock
      3. Groq -> Heurística local ou LLM disponível -> Mock
    """
    ...
```

### 2.3. Grafo de Estados Unificado (`backend/app/agent/graph.py`)

Estruturaremos o fluxo em um `StateGraph` do LangGraph com nós independentes:

```python
# backend/app/agent/state.py

class AgentGraphState(TypedDict, total=False):
    # Entradas de contexto
    user_id: str
    lesson_id: str
    exercise_id: int | None
    student_name: str
    module_title: str
    lesson_title: str
    
    # Roteamento
    action_type: Literal["generate_lesson", "evaluate_exercise"]
    
    # Dados da Lição
    lesson_content: LessonContent | None
    
    # Dados da Avaliação
    exercise_question: str | None
    expected_answer: str | None
    student_submission: str | None
    evaluation_result: ExerciseEvaluationResponse | None
```

**Nós do Grafo:**
1. **`router_node`:** Analisa a entrada via Groq (ou classificação determinística por rota da API) e define a próxima ramificação.
2. **`tutor_node`:** Dispara o prompt do *Magister Latium* no Claude 3.5 Sonnet estruturado via `.with_structured_output(LessonContent)`.
3. **`evaluator_node`:** Dispara o prompt do *Censor Latium* no GPT-4o estruturado via `.with_structured_output(ExerciseEvaluationResponse)`.

---

## 3. Schemas Pydantic do Agente Avaliador

Criaremos o arquivo `backend/app/schemas/evaluation.py` definindo a estrutura de correção e feedback:

```python
from pydantic import BaseModel, Field

class MorphologicalToken(BaseModel):
    """Análise gramatical de um termo individual submetido pelo aluno."""
    token: str = Field(description="A palavra ou termo analisado")
    lemma: str = Field(description="Entrada de dicionário / lema (ex: puella, amare)")
    part_of_speech: str = Field(description="Classe gramatical (substantivo, adjetivo, verbo, preposição, etc.)")
    grammatical_features: str = Field(description="Caso, gênero, número, tempo, modo, pessoa (ex: Nominativo Feminino Singular)")
    is_correct: bool = Field(description="Indica se a flexão/termo foi empregado corretamente no contexto")
    feedback_note: str | None = Field(default=None, description="Observação específica sobre a palavra se houver erro")

class ExerciseEvaluationRequest(BaseModel):
    """Payload de submissão do exercício para correção pelo Agente Avaliador."""
    lesson_id: str = Field(description="Identificador da lição ativa")
    exercise_id: int = Field(description="Identificador do exercício na lição")
    question: str = Field(description="Enunciado ou frase em latim/português")
    expected_answer: str = Field(description="Resposta de referência clássica")
    student_answer: str = Field(description="Texto submetido pelo aluno")
    exercise_type: str = Field(default="translation", description="Tipo de exercício (translation, composition, fill_blank)")

class ExerciseEvaluationResponse(BaseModel):
    """Resultado estruturado gerado pelo Agente Avaliador (GPT-4o)."""
    is_correct: bool = Field(description="Verdadeiro se a resposta estiver substancialmente correta")
    score: int = Field(ge=0, le=100, description="Nota de 0 a 100 baseada em critérios clássicos")
    overall_feedback: str = Field(description="Parecer geral humanista sobre a resolução do aluno")
    syntax_critique: str = Field(description="Análise da estrutura sintática e ordem das palavras (SOV vs SVO)")
    morphological_breakdown: list[MorphologicalToken] = Field(
        default_factory=list,
        description="Decomposição morfológica detalhada palavra por palavra"
    )
    suggested_classical_alternatives: list[str] = Field(
        default_factory=list,
        description="Variações clássicas elegantes (ex: 'Ciceroniano' vs 'Vulgar')"
    )
    evaluator_model: str = Field(description="Nome do modelo de IA que realizou a correção (ex: gpt-4o)")
```

---

## 4. Atualizações na API Backend

### 4.1. Novo Endpoint no FastAPI
* **Rota:** `POST /api/v1/lessons/{lesson_id}/evaluate`
* **Autenticação:** Protegida via JWT (`get_current_user`).
* **Comportamento:**
  - Recebe o `ExerciseEvaluationRequest`.
  - Executa o Agente Avaliador através do LangGraph.
  - Registra telemetria de acerto para o histórico do aluno.
  - Retorna o `ExerciseEvaluationResponse` com latência otimizada.

### 4.2. Novas Variáveis de Ambiente em `app/core/config.py` e `.env`
* `ANTHROPIC_API_KEY`: Chave de API da Anthropic (Claude 3.5).
* `OPENAI_API_KEY`: Chave de API da OpenAI (GPT-4o).
* `GROQ_API_KEY`: Chave de API da Groq (Llama 3.1).
* `EVALUATOR_MODEL`: Nome do modelo (padrão `gpt-4o` com fallback automático para `gpt-4o-mini` ou `mock`).
* `TUTOR_MODEL`: Nome do modelo (padrão `claude-3-5-sonnet-20241022` com fallback para `gemini-1.5-pro` ou `mock`).

---

## 5. Modificações na Interface React (`frontend/`)

### 5.1. Novos Tipos e Chamada de API
1. **`frontend/src/types/evaluation.ts`:**
   - Tipos TypeScript correspondentes ao `ExerciseEvaluationRequest` e `ExerciseEvaluationResponse`.
2. **`frontend/src/api/lessonApi.ts`:**
   - Adicionar método `evaluateExercise(lessonId, payload)`.

### 5.2. Componente de Feedback no `ClassroomPage.tsx`
Atualmente, as perguntas de texto livre (`translation` / `fill_blank`) comparam apenas igualdade estrita de strings. Na Fase 4:
1. **Botão "Submeter ao Avaliador IA":**
   - Ativa estado de carregamento com micro-animação (*"Consultando o Censor Latium..."*).
2. **Card de Decomposição Morfológica (Interactive Token Pills):**
   - Cada palavra digitada pelo aluno é renderizada em uma "pílula" interativa:
     - Verde: concordância correta (ex: *Nominativo Singular Feminino*).
     - Vermelha/Âmbar: erro de caso, desinência ou lema incorreto.
   - Ao tocar/passar o mouse sobre a palavra, abre um mini popover explicativo.
3. **Painel de Estilo e Sintaxe Clássica:**
   - Comentário sintático (ex: *"Bom uso do acusativo, porém em Latim clássico o verbo costuma encerrar a oração"*).
   - Caixa expansível com variações estilísticas consagradas em textos de Cícero ou Virgílio.
4. **Integração na Pontuação Geral:**
   - A nota atribuída pelo Avaliador (ex: 85/100) é incorporada dinamicamente à média da lição para submissão final via `/complete`.

---

## 6. Arquitetura de Testes e Validação da Fase 4

1. **Testes Unitários e de Integração no Backend (`pytest`):**
   - Teste de instanciação da fábrica multi-modelo (`test_llm_factory.py`).
   - Teste de correção gramatical com o Agente Avaliador (`test_evaluator_agent.py`):
     - Validação de resposta 100% correta.
     - Validação de resposta com erro de caso (ex: acusativo usado no lugar de nominativo).
     - Validação de fallback offline determinístico para o mock avaliador.
   - Teste da rota `POST /api/v1/lessons/{lesson_id}/evaluate`.
2. **TypeScript & Frontend Build:**
   - Garantir que `tsc && vite build` continue passando com 0 erros de tipagem.
3. **Execução de E2E:**
   - Script automatizado testando o ciclo: Login -> Gerar Lição -> Submeter Exercício Aberto ao Avaliador -> Receber Decomposição Morfológica -> Concluir Lição.

---

## 7. Próximos Passos (Aguardando Aprovação)

Uma vez revisado e aprovado pelo Tech Lead, a execução seguirá na ordem:
1. Adicionar dependências (`langchain-anthropic`, `langchain-groq`) e atualizar configurações.
2. Implementar `llm_factory.py`, schemas do avaliador e o novo nó no LangGraph.
3. Criar a rota no FastAPI e cobrir com testes Pytest.
4. Implementar os componentes no React e validar a experiência de uso.

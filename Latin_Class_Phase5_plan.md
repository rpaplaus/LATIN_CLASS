# Plano da Fase 5: A Biblioteca de Alexandria (RAG com pgvector)

**Documento de Planejamento de Engenharia e Arquitetura**  
**Projeto:** Latium AI  
**Versão:** 1.0  
**Status:** Aguardando Aprovação do Tech Lead (System Halt Ativo)  

---

## 1. Visão Geral e Objetivos da Fase 5

Nas Fases 1 a 4, consolidamos o backend com FastAPI, PostgreSQL, Redis, autenticação por Refresh Token Rotation, interface móvel em React e o Agente Avaliador com arquitetura multi-modelo.

O objetivo da **Fase 5** é conceder **memória de longo prazo, erudição literária e embasamento histórico** ao *Magister Latium*. Através de uma arquitetura **RAG (Retrieval-Augmented Generation)** utilizando a extensão vetorial **`pgvector`** (já ativada no PostgreSQL 16), o professor de Latim poderá consultar em tempo real a *Biblioteca de Alexandria*:
1. Consultar textos literários canônicos (ex: *De Bello Gallico* de Júlio César, *In Catilinam* de Cícero).
2. Consultar compêndios gramaticais de referência (morfologia, sintaxe de casos e regras de exceção).
3. Utilizar uma ferramenta de busca semântica (*Retriever Tool*) integrada ao LangGraph para trazer trechos autênticos à sala de aula.

---

## 2. Modelagem das Tabelas no SQLAlchemy com `pgvector`

### 2.1. Dependência e Tipo Vetorial
Utilizaremos a biblioteca oficial [`pgvector`](https://github.com/pgvector/pgvector-python) integrada ao SQLAlchemy 2.0:
```python
from pgvector.sqlalchemy import Vector
```
A extensão `vector` já foi habilitada no PostgreSQL na migração `0001_initial_users.py`.

### 2.2. Novas Tabelas: `library_documents` e `document_chunks`

Criaremos o arquivo [`backend/app/models/rag.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/models/rag.py):

```python
# backend/app/models/rag.py
import uuid
from typing import Any
from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

class LibraryDocument(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Representa uma obra ou livro canônico presente na Biblioteca de Alexandria."""

    __tablename__ = "library_documents"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    era_category: Mapped[str] = mapped_column(
        String(50), nullable=False, default="Classical", index=True
    )  # ex: Classical, Vulgar, Medieval, Grammar
    source_language: Mapped[str] = mapped_column(String(10), nullable=False, default="la")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB, nullable=True)

    # Relacionamento 1:N com fragmentos indexados
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentChunk.chunk_index",
    )


class DocumentChunk(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Fragmento (chunk) textual com vetor de embedding para busca semântica."""

    __tablename__ = "document_chunks"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("library_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)  # Trecho original em latim ou regra
    translation: Mapped[str | None] = mapped_column(Text, nullable=True)  # Tradução para português
    citation: Mapped[str] = mapped_column(String(150), nullable=False)  # ex: "Caes. Gal. 1.1"
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB, nullable=True)

    # Coluna vetorial com dimensão padrão 1536 (text-embedding-3-small)
    embedding: Mapped[list[float]] = mapped_column(Vector(1536), nullable=False)

    document: Mapped["LibraryDocument"] = relationship(
        "LibraryDocument", back_populates="chunks"
    )

    __table_args__ = (
        # Índice HNSW para busca por distância de cosseno em altíssima velocidade
        Index(
            "ix_document_chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )
```

### 2.3. Migração Alembic (`0003_alexandria_library_rag.py`)
- Criação das tabelas `library_documents` e `document_chunks`.
- Configuração do índice HNSW com `vector_cosine_ops`.
- Chaves estrangeiras com `ON DELETE CASCADE`.

---

## 3. Modelo de Embeddings Sugerido

### 3.1. Recomendação Padrão: `text-embedding-3-small` (OpenAI)
* **Dimensão:** `1536` dimensões (com excelente compressão e capacidade de captura sintática).
* **Por que esta escolha?**
  1. **Acurácia em Línguas Mortas/Clássicas:** O modelo `text-embedding-3-small` demonstrou desempenho superior na captura de desinências casuais e vocabulário latino em comparação a modelos menores legados.
  2. **Custo Extremamente Acessível:** Custa apenas US$ 0,02 por milhão de tokens (tornando a indexação de obras inteiras praticamente gratuita).
  3. **Compatibilidade:** Suporte de primeira classe nativo via `langchain-openai`.

### 3.2. Alternativas e Cascata de Fallback
Para manter o princípio multi-modelo consolidado na Fase 4, a fábrica de embeddings em [`app/agent/llm_factory.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/agent/llm_factory.py) suportará:
1. **OpenAI (`text-embedding-3-small`, 1536d):** Padrão primário quando `OPENAI_API_KEY` estiver configurada.
2. **Google Gemini (`text-embedding-004`):** Provedor alternativo via `langchain-google-genai`.
3. **Mock Embeddings Determinístico (*Offline/CI*):** Gerador local baseado em hashing semântico normalizado (`L2 normalized`). Permite que toda a suíte de testes de RAG rode nos runners do GitHub Actions e localmente com **custo zero e sem depender de chaves externas**.

### 3.3. Configurações em `app/core/config.py`
* `EMBEDDING_PROVIDER: str = "openai"` (ou `"gemini"`, `"mock"`)
* `EMBEDDING_MODEL: str = "text-embedding-3-small"`
* `EMBEDDING_DIMENSION: int = 1536`

---

## 4. Pipeline de Ingestão (ETL) e Corpus Canônico

### 4.1. Módulo de Chunking Inteligente (`backend/app/rag/ingestion.py`)
Textos clássicos em latim não devem ser divididos arbitrariamente no meio de orações para não quebrar concordâncias de casos. O pipeline implementará:
- Divisão respeitando parágrafos e pontuação clássica latina (pontos finais, ponto-e-vírgula e marcações de capítulo).
- Associação do trecho em latim com sua respectiva tradução/anotação gramatical.
- Extração de metadados canônicos: Autor, Obra, Livro, Capítulo e Tópicos Gramaticais presentes.

### 4.2. Corpus Inicial de Alexandria (Seed Data)
Incluiremos arquivos de dados em `backend/app/rag/corpus/`:
1. **Júlio César — *Commentarii de Bello Gallico* (Livro I):**
   * Trechos clássicos de estratégia militar e geografia da Gália (*"Gallia est omnis divisa in partes tres..."*).
2. **Marco Túlio Cícero — *In Catilinam I*:**
   * Trechos essenciais de oratória romana e retórica política (*"Quo usque tandem abutere, Catilina, patientia nostra?"*).
3. **Gramática Latina Sistemática (Sintaxe dos Casos):**
   * Regras do Nominativo, Acusativo, Ablativo Absoluto e Conjugação Perifrástica.

### 4.3. Script Executável
`scripts/ingest_corpus.py` para popular o banco via CLI ou endpoint administrativo `POST /api/v1/admin/rag/ingest`.

---

## 5. Integração da Tool de Busca Semântica no LangGraph

### 5.1. Implementação do Retriever Vetorial
Função assíncrona que calcula a similaridade por cosseno diretamente no PostgreSQL:

```python
# backend/app/rag/retriever.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.rag import DocumentChunk, LibraryDocument

async def search_library_chunks(
    db: AsyncSession,
    query_vector: list[float],
    top_k: int = 3,
    author_filter: str | None = None,
) -> list[dict[str, Any]]:
    """Busca os trechos clássicos mais similares utilizando distância de cosseno no pgvector."""
    stmt = (
        select(DocumentChunk, LibraryDocument)
        .join(LibraryDocument, DocumentChunk.document_id == LibraryDocument.id)
        .order_by(DocumentChunk.embedding.cosine_distance(query_vector))
        .limit(top_k)
    )
    if author_filter:
        stmt = stmt.where(LibraryDocument.author.ilike(f"%{author_filter}%"))
    
    result = await db.execute(stmt)
    ...
```

### 5.2. A Ferramenta do Agente: `search_latin_library`
Criaremos o arquivo [`backend/app/agent/tools.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/agent/tools.py):

```python
from langchain_core.tools import tool

@tool
async def search_latin_library(query: str, author: str | None = None) -> str:
    """
    Pesquisa na Biblioteca de Alexandria por textos originais em latim, 
    traduções e regras gramaticais de autores clássicos (César, Cícero, Horácio).
    Use esta ferramenta quando precisar de citações autênticas, exemplos históricos 
    ou embasamento sobre táticas romanas, política e gramática.
    """
    ...
```

### 5.3. Integração com o Nó do Tutor no LangGraph

Atualizaremos o grafo em [`backend/app/agent/graph.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/agent/graph.py):

```
                        [ Requisição do Aluno ]
                                   │
                                   ▼
                         ┌───────────────────┐
                         │    router_node    │
                         └─────────┬─────────┘
                                   │
                 ┌─────────────────┴─────────────────┐
                 │                                   │
                 ▼                                   ▼
       ┌───────────────────┐               ┌───────────────────┐
       │    tutor_node     │               │  evaluator_node   │
       │ (Claude 3.5 +     │               │     (GPT-4o)      │
       │  Alexandria Tool) │               └───────────────────┘
       └─────────┬─────────┘
                 │
                 ▼ [Tool Call: se necessário embasamento]
       ┌───────────────────┐
       │   rag_tool_node   │ (Busca vetorial no pgvector)
       └─────────┬─────────┘
                 │
                 ▼ [Retorna com trechos de César/Cícero]
       ┌───────────────────┐
       │   tutor_node      │ (Sintetiza a aula com exemplos autênticos)
       └───────────────────┘
```

**Estratégia Híbrida Inteligente:**
1. **Pre-retrieval Contextual:** Quando a lição tem um objetivo histórico definido (ex: "Módulo I: Geografia e Guerras de Roma"), o nó do tutor injeta automaticamente os 2 trechos mais pertinentes de César no prompt de sistema.
2. **Tool Calling ReAct Dinâmico:** Se o aluno fizer perguntas específicas ou quando o modelo julgar necessário aprofundar uma citação latina, ele invoca a ferramenta `search_latin_library` para consultar a Biblioteca de Alexandria antes de responder.

---

## 6. Plano de Testes e Validação da Fase 5

1. **Testes de Migração e Banco de Dados (PostgreSQL + pgvector):**
   * Aplicação da nova migração Alembic.
   * Validação de inserção e consulta de vetores com `Vector(1536)` e operador `<=>` (cosine distance).
2. **Testes Unitários da Fábrica de Embeddings:**
   * Validação de geração de embeddings com modelo online e mock determinístico.
3. **Testes do Pipeline de Ingestão:**
   * Ingestão de trecho do *De Bello Gallico* e verificação dos chunks criados no banco.
4. **Testes de Busca Semântica (Retriever Tool):**
   * Busca por termo "Gália dividida em três partes" retornando o chunk correto de Júlio César com alta similaridade.
5. **Execução de Suíte Completa:**
   * `pytest` cobrindo os novos testes.
   * `mypy` estrito mantendo zero erros.
   * `ruff` linter e formatação.

---

## 7. Próximos Passos (Aguardando Aprovação)

Uma vez revisado e aprovado pelo Tech Lead, executaremos:
1. Instalação do pacote `pgvector` no Python virtualenv e dependências em `pyproject.toml`.
2. Criação dos modelos em `app/models/rag.py` e migração Alembic.
3. Implementação da fábrica de embeddings e pipeline de ingestão com corpus semente.
4. Criação da Tool e conexão com o nó do tutor no LangGraph.
5. Execução de testes de validação e emissão do walkthrough da Fase 5.

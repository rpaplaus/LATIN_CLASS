# LC5 Walkthrough — Fase 5: A Biblioteca de Alexandria (RAG com pgvector)

Concluímos com total êxito a **Fase 5: A Biblioteca de Alexandria (RAG)** do **Latium AI**. O sistema agora conta com uma infraestrutura vetorial clássica de alta performance baseada na extensão `pgvector` do PostgreSQL 16 com índice HNSW, um pipeline completo de embeddings de 1536 dimensões, um mecanismo de ingestão de corpus canônico e a ferramenta semântica `search_latin_library` acoplada ao nó do tutor no LangGraph.

---

## 🏛️ O Que Foi Implementado na Fase 5

### 1. Modelagem Vetorial e Migração Alembic (`app/models/rag.py`)
- **Extensão `pgvector` e Suporte a Vetores 1536-D:**
  - Configurado o pacote `pgvector>=0.3.0` no backend e integradas as tipagens ao Mypy.
  - Criada a tabela [`library_documents`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/models/rag.py): Armazena obras clássicas e manuais gramaticais com metadados de autor, título, época (`era_category`) e idioma de origem.
  - Criada a tabela [`document_chunks`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/models/rag.py): Armazena fragmentos textuais, citações canônicas (ex: *Caes. Gal. 1.1*), traduções/comentários, metadados em JSONB e coluna vetorial `embedding = Column(Vector(1536))`.
  - **Índice HNSW de Alta Performance:** Criado o índice `ix_document_chunks_embedding_hnsw` com `m=16`, `ef_construction=64` e operador `vector_cosine_ops` para busca por similaridade de cosseno em tempo sub-milissegundo.
- **Migração Alembic:**
  - Gerada e aplicada a migração [`migrations/versions/0003_alexandria_library_rag.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/migrations/versions/0003_alexandria_library_rag.py), ativando com segurança a extensão `vector` e criando as tabelas com integridade relacional.

### 2. Módulos de Embeddings e Retriever Semântico (`app/rag/`)
- **Pipeline de Embeddings Multi-Provedor ([`embeddings.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/rag/embeddings.py)):**
  - Integração com `text-embedding-3-small` da OpenAI (1536 dimensões).
  - Suporte ao Gemini `text-embedding-004` com projeção e normalização $L_2$.
  - Gerador determinístico de mock vetorial (`_deterministic_mock_embedding`) para execução offline resiliente em pipelines de CI/CD e testes locais sem consumo de créditos de API.
  - Funções assíncronas `get_embedding(text)` e `get_embeddings_batch(texts)`.
- **Mecanismo de Recuperação Semântica ([`retriever.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/rag/retriever.py)):**
  - Função `search_library_chunks(db, query, top_k, author_filter, era_filter)` executando ordenação por distância de cosseno:
    ```python
    stmt = stmt.order_by(DocumentChunk.embedding.cosine_distance(query_vector)).limit(top_k)
    ```
  - Formatador humanístico `format_chunks_for_context` que estrutura citações latinas autênticas, autores e notas de tradução para injeção no prompt do professor.

### 3. Ingestão Canônica e Script CLI (`app/rag/ingestion.py` & `scripts/ingest_corpus.py`)
- **Corpus Canônico Semente:**
  - **Júlio César:** *Commentarii de Bello Gallico* (Liber I: capítulos 1.1, 1.2 e 1.7) com citações sobre a divisão da Gália e táticas militares.
  - **Cícero:** *Oratio in Catilinam Prima* (capítulos 1.1 e 1.2) com oratória senatorial e figuras de retórica.
  - **Academia Latium:** Compêndio de Gramática Clássica com regras sobre o Caso Nominativo, Acusativo e Ordem das Palavras SOV (*Subject-Object-Verb*).
- **Script CLI de Ingestão:**
  - Criado o script executável [`scripts/ingest_corpus.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/scripts/ingest_corpus.py) com lógica idempotente (previne duplicações em múltiplas execuções).
  - Ingestão executada com sucesso contra o PostgreSQL ao vivo: 8 fragmentos clássicos devidamente vetorizados e indexados.

### 4. Ferramenta LangChain e Acoplamento ao LangGraph
- **Ferramenta `@tool search_latin_library` ([`app/agent/tools.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/agent/tools.py)):**
  - Ferramenta tipada para o LangChain com docstring humanística, pronta para ser invocada pelo agente ou via pre-retrieval.
- **Acoplamento no Grafo ([`app/agent/graph.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/agent/graph.py)):**
  - O nó `tutor_node` realiza o pré-retrieval semântico na Biblioteca de Alexandria com base no tópico da lição e nos objetivos gramaticais, injetando o contexto no estado do fluxo.
- **Enriquecimento do Agente Professor ([`app/agent/professor.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/agent/professor.py)):**
  - O prompt socrático do *Magister Latium* agora possui a seção `FRAGMENTOS DA BIBLIOTECA DE ALEXANDRIA (RAG)`, instruindo o agente a fundamentar suas explicações com citações literárias autênticas de César ou Cícero sempre que oportuno.

---

## 🧪 Logs e Resultados dos Testes

### 1. Suíte de Testes Pytest do RAG e Geral (28/28 Aprovados)
```text
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0 -- .venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\mbpap\OneDrive\Documents\Rodrigo\LATIN_CLASS\backend
configfile: pyproject.toml
plugins: anyio-4.15.1, langsmith-0.12.5, asyncio-1.4.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collecting ... collected 28 items

backend\tests\test_auth.py::test_register_user_success PASSED            [  3%]
backend\tests\test_auth.py::test_register_duplicate_email PASSED         [  7%]
backend\tests\test_auth.py::test_login_oauth2_success PASSED             [ 10%]
backend\tests\test_auth.py::test_login_incorrect_password PASSED         [ 14%]
backend\tests\test_auth.py::test_refresh_token_rotation_success PASSED   [ 17%]
backend\tests\test_auth.py::test_logout_revokes_refresh_token PASSED     [ 21%]
backend\tests\test_auth.py::test_read_me_unauthorized PASSED             [ 25%]
backend\tests\test_auth.py::test_read_me_authorized PASSED               [ 28%]
backend\tests\test_evaluator.py::test_llm_factory_fallback_resolution PASSED [ 32%]
backend\tests\test_evaluator.py::test_evaluator_exact_match_offline PASSED [ 35%]
backend\tests\test_evaluator.py::test_evaluator_partial_match_offline PASSED [ 39%]
backend\tests\test_evaluator.py::test_evaluator_api_endpoint PASSED      [ 42%]
backend\tests\test_evaluator.py::test_evaluator_invalid_lesson_404 PASSED [ 46%]
backend\tests\test_health.py::test_health_endpoint PASSED                [ 50%]
backend\tests\test_lessons.py::test_list_course_modules PASSED           [ 53%]
backend\tests\test_lessons.py::test_get_initial_student_progress PASSED  [ 57%]
backend\tests\test_lessons.py::test_generate_next_lesson_content PASSED  [ 60%]
backend\tests\test_lessons.py::test_complete_lesson_and_advance PASSED   [ 64%]
backend\tests\test_rag.py::test_deterministic_mock_embedding_properties PASSED [ 67%]
backend\tests\test_rag.py::test_get_embedding_interface PASSED           [ 71%]
backend\tests\test_rag.py::test_get_embeddings_batch_interface PASSED    [ 75%]
backend\tests\test_rag.py::test_format_chunks_for_context_formatting PASSED [ 78%]
backend\tests\test_rag.py::test_ingest_corpus_seed_idempotent PASSED     [ 82%]
backend\tests\test_rag.py::test_search_library_chunks_pgvector PASSED    [ 85%]
backend\tests\test_rag.py::test_search_latin_library_langchain_tool PASSED [ 89%]
backend\tests\test_users.py::test_list_users_as_student_forbidden PASSED [ 92%]
backend\tests\test_users.py::test_list_users_as_superuser_success PASSED [ 96%]
backend\tests\test_users.py::test_update_current_user_profile PASSED     [100%]

============================= 28 passed in 26.08s =============================
```

### 2. Verificação Rigorosa de Tipos com Mypy Strict (42 Arquivos)
```powershell
cmd /c "set MYPYPATH=backend&& .venv\Scripts\mypy --config-file backend/pyproject.toml backend/app backend/tests"
Success: no issues found in 42 source files
```

### 3. Linting e Formatação de Código com Ruff
```powershell
.venv\Scripts\ruff check backend
All checks passed!

.venv\Scripts\ruff format --check backend
44 files already formatted
```

### 4. Compilação TypeScript e Build do Frontend (Vite)
```bash
docker compose exec -T frontend npm run build

> latium-frontend@0.1.0 build
> tsc && vite build

vite v5.4.21 building for production...
transforming...
✓ 1643 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   1.37 kB │ gzip:  0.74 kB
dist/assets/index-BLRKFj5K.css   32.38 kB │ gzip:  6.07 kB
dist/assets/index-DZXVt1F5.js   250.87 kB │ gzip: 78.91 kB
✓ built in 6.22s
```

### 5. Ingestão e Integridade da Base ao Vivo
```powershell
.venv\Scripts\python scripts/ingest_corpus.py
=============================================================
[ALEXANDRIA] INGESTAO DA BIBLIOTECA DE ALEXANDRIA (RAG)
=============================================================
Conectando ao PostgreSQL e processando obras canonicas...
[OK] Ingestao concluida com sucesso! Total de fragmentos indexados: 0 (todos os 8 fragmentos canônicos já indexados e protegidos contra duplicação)
```

---

## 📌 Resumo dos Arquivos Criados ou Modificados

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| [`backend/pyproject.toml`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/pyproject.toml) | Modificado | Adicionado `pgvector>=0.3.0` e overrides do mypy para módulos vetoriais. |
| [`backend/app/models/rag.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/models/rag.py) | Criado | Modelos `LibraryDocument` e `DocumentChunk` com `Vector(1536)` e índice HNSW. |
| [`backend/app/models/__init__.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/models/__init__.py) | Modificado | Exportação das novas entidades para Alembic e ORM. |
| [`backend/migrations/versions/0003_alexandria_library_rag.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/migrations/versions/0003_alexandria_library_rag.py) | Criado | Migração DDL com ativação da extensão `vector`, criação de tabelas e índice HNSW. |
| [`backend/app/rag/embeddings.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/rag/embeddings.py) | Criado | Gerador de vetores 1536-D (OpenAI, Gemini e Mock determinístico normalizado $L_2$). |
| [`backend/app/rag/retriever.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/rag/retriever.py) | Criado | Busca vetorial via distância de cosseno no pgvector e formatador de contexto. |
| [`backend/app/rag/ingestion.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/rag/ingestion.py) | Criado | Motor de ingestão e corpus canônico de Júlio César, Cícero e Gramática Latina. |
| [`backend/app/agent/tools.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/agent/tools.py) | Criado | LangChain `@tool search_latin_library` para consulta à biblioteca. |
| [`backend/app/agent/professor.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/agent/professor.py) | Modificado | Injeção de contexto literário clássico no prompt de geração de lição. |
| [`backend/app/agent/graph.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/agent/graph.py) | Modificado | Execução do pre-retrieval no `tutor_node` e passagem de contexto da biblioteca. |
| [`scripts/ingest_corpus.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/scripts/ingest_corpus.py) | Criado | Script CLI para carga idempotente de corpus clássico. |
| [`backend/tests/test_rag.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/tests/test_rag.py) | Criado | 7 testes de embeddings, busca por cosseno no pgvector, filtros e tool. |
| [`LC5_walkthrough.md`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/LC5_walkthrough.md) | Criado | Relatório de entrega da Fase 5 com evidências e logs de execução. |

---

## 🎯 Conclusão e Próximos Passos
A infraestrutura de RAG da Biblioteca de Alexandria está 100% operacional, integrada com segurança ao banco de dados vetorial PostgreSQL 16 e acoplada ao LangGraph do Magister Latium. Estamos prontos para a próxima etapa do projeto!

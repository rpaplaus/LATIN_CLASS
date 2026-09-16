# 🛡️ Relatório de Auditoria Técnica & Plano de Refatoração — Fase 7: Zero Dívida Técnica

> **Latium AI — Plataforma de Ensino Inteligente de Latim**  
> **Classificação:** Auditoria Arquitetural, Segurança, Performance e Confiabilidade  
> **Status:** Proposta de Refatoração (Aguardando Aprovação do Tech Lead)  
> **Data:** Setembro de 2026  
> **Autor:** Auditoria Técnica Especializada / Antigravity AI  

---

## 1. Sumário Executivo

Ao longo das Fases 1 a 6, o **Latium AI** evoluiu rapidamente de uma estrutura fundamental com FastAPI e PostgreSQL/pgvector para uma plataforma educacional completa de alto valor agregado:
- Orquestração multi-modelo com múltiplos agentes de IA especializados (Magister Latium, Censor Avaliador com decomposição morfológica, RAG da Biblioteca de Alexandria e Ilustrador SVG);
- Motor de áudio dual-cache com síntese fonética de Latim Clássico e Restituído;
- Gamificação interativa inspirada na hierarquia e nos ritos do Senado Romano;
- Frontend interativo em React 18, Vite e Tailwind CSS, otimizado para navegadores desktop e Safari no iOS.

Embora o ecossistema conte com 40 testes unitários e de integração passando e 100% de conformidade de tipagem no Mypy, o ritmo acelerado de entrega acumulou débitos técnicos que precisam ser eliminados antes do lançamento em ambiente produtivo de alta escala.

Esta auditoria realizou um **"pente fino" cirúrgico** em toda a arquitetura, identificando **17 pontos de melhoria e vulnerabilidades potenciais**, organizados em 4 pilares:
1. **Segurança e Estado** (Autenticação, Ciclo de Vida JWT, Secrets e Headers);
2. **Performance e Banco de Dados** (Event Loop, Redis Pooling, pgvector HNSW e Queries N+1);
3. **Qualidade de Código e CI/CD** (Ruff, Mypy estrito e Automação no GitHub Actions);
4. **Frontend e UX** (Code-Splitting, Otimização de Re-renders e Gestão de Interceptor HTTP).

---

## 2. Diagnóstico Detalhado por Pilar

```
====================================================================================================
PILAR 1: SEGURANÇA E ESTADO (Autenticação, Ciclo de Vida JWT, Secrets e Headers)
====================================================================================================
```

### [SEC-01] Ausência de Rate Limiting em Endpoints Críticos de Autenticação
- **Localização:** [`backend/app/api/v1/endpoints/auth.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/api/v1/endpoints/auth.py) (`/register` e `/login`).
- **Problema:** Não há contenção automatizada de requisições concorrentes por IP ou por conta. Atacantes podem executar força bruta (*credential stuffing*, adivinhação de senhas com dicionário) ou esgotar recursos com criação em massa de contas fictícias.
- **Risco:** **Alto** (Comprometimento de contas de usuários, exaustão do pool de conexões do banco e negação de serviço).
- **Proposta Exata de Refatoração:**
  1. Criar um utilitário centralizado de controle de taxa [`backend/app/core/rate_limit.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/core/rate_limit.py) operando com contadores atômicos no Redis via `INCR` e `EXPIRE`.
  2. Implementar extração resiliente de IP considerando cabeçalhos de proxy reverso (`X-Forwarded-For` ou `request.client.host`).
  3. Definir limites configuráveis via `Settings`:
     - Máximo de **10 tentativas de login por minuto por IP** (`RATE_LIMIT_LOGIN_MAX`).
     - Máximo de **5 registros de conta por minuto por IP** (`RATE_LIMIT_REGISTER_MAX`).
  4. Retornar `HTTP 429 Too Many Requests` com cabeçalho padrão `Retry-After` informando os segundos restantes para liberação.

---

### [SEC-02] Ciclo de Vida do JWT: Armazenamento no Navegador e Prevenção de Roubo de Sessão
- **Localização:** [`frontend/src/api/client.ts`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/frontend/src/api/client.ts) e [`backend/app/core/redis.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/core/redis.py).
- **Problema:**
  - O Access Token é adequadamente mantido apenas em memória (`inMemoryAccessToken`). No entanto, o Refresh Token reside em `localStorage`. Qualquer vulnerabilidade de injeção de script (XSS) ou pacote npm de terceiros malicioso pode extrair o token persistente.
  - No backend, sem uma política de detecção de reuso (*Reuse Detection / Revocation Cascading*), um refresh token roubado pode ser utilizado concorrentemente com o do usuário legítimo sem detecção imediata.
- **Risco:** **Médio-Alto** (Sequestro prolongado de sessão e reuso ilícito de credenciais).
- **Proposta Exata de Refatoração:**
  1. **Detecção de Reuso de Refresh Token no Redis:**
     - Ao emitir um Refresh Token, gravar seu JTI com status `"active"` e TTL no Redis (`refresh_token:{user_id}:{jti}`).
     - Ao rotacionar no endpoint `/auth/refresh`, marcar o JTI consumido como `"revoked"` em uma blacklist temporária (`revoked_token:{user_id}:{jti}`) com TTL defensivo de 1 hora.
     - Se uma requisição apresentar um JTI com status `"revoked"`, disparar o gatilho de violação: invalidar imediatamente todas as sessões ativas do usuário (`revoke_all_user_tokens`) no Redis e exigir reautenticação com senha.
  2. **Evolução Arquitetural de Armazenamento:**
     - Em fase subsequente, transicionar o Refresh Token para Cookie `HttpOnly`, `Secure`, `SameSite=Strict`, eliminando qualquer superfície de leitura via JavaScript no cliente.

---

### [SEC-03] Ausência de Cabeçalhos HTTP Defensivos (Security Headers)
- **Localização:** [`backend/app/main.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/main.py).
- **Problema:** A aplicação FastAPI implementa apenas `CORSMiddleware`. Faltam cabeçalhos HTTP que instruem navegadores modernos (incluindo Mobile Safari) a bloquear ataques estruturais como Clickjacking, MIME-sniffing e injeção de iframes.
- **Risco:** **Médio** (Vulnerabilidade a Clickjacking em iframes e ataques de MIME-type confusion).
- **Proposta Exata de Refatoração:**
  1. Criar o middleware [`backend/app/core/middleware.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/core/middleware.py) (`SecurityHeadersMiddleware`) injetando nos responses:
     - `X-Content-Type-Options: nosniff` (impede browsers de interpretarem scripts mascarados como imagens);
     - `X-Frame-Options: DENY` (bloqueia incorporação do Latium AI em iframes externos);
     - `X-XSS-Protection: 1; mode=block` (filtro defensivo para navegadores legados);
     - `Referrer-Policy: strict-origin-when-cross-origin` (previne vazamento de URLs internas em requisições externas);
     - `Permissions-Policy: geolocation=(), microphone=(), camera=()` (bloqueia sensores desnecessários);
     - `Strict-Transport-Security: max-age=31536000; includeSubDomains` (forçado quando em ambiente de produção).
  2. Registrar o middleware antes das rotas no `main.py`.

---

### [SEC-04] Segredo Criptográfico Padrão em `config.py` sem Bloqueio em Produção
- **Localização:** [`backend/app/core/config.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/core/config.py).
- **Problema:** A variável `SECRET_KEY` possui valor padrão `"insecure-dev-secret-key-..."`. Se a aplicação for implantada com `ENVIRONMENT=production` sem fornecer uma chave forte no `.env`, o sistema sobe sem alertas, permitindo a forja de JWTs por terceiros.
- **Risco:** **Crítico** (Falsificação de assinatura de tokens de autenticação se esquecida em produção).
- **Proposta Exata de Refatoração:**
  1. Adicionar um `@model_validator(mode="after")` em `Settings` no Pydantic v2.
  2. Se `ENVIRONMENT in ("production", "prod")`, verificar se a chave contém o termo `"insecure"` ou se possui entropia inferior a 32 caracteres.
  3. Lançar `ValueError` fatal que aborta imediatamente o processo de inicialização do servidor Uvicorn caso a validação falhe.

---

### [SEC-05] Sanitização de SVGs Gerados por IA contra Stored XSS
- **Localização:** [`backend/app/agent/illustrator.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/agent/illustrator.py) e [`backend/app/api/v1/endpoints/media.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/api/v1/endpoints/media.py).
- **Problema:** O agente Ilustrador gera vetores SVG sintéticos a partir de prompts LLM e os salva em disco. Arquivos SVG podem conter tags `<script>`, links `javascript:...` ou manipuladores de eventos (`onload`, `onerror`). Se servidos com `Content-Type: image/svg+xml` sem sanitização rigorosa, a abertura direta do SVG no navegador executa código arbitrário no contexto de origem.
- **Risco:** **Médio-Alto** (Stored XSS através de ilustrações geradas pelo agente de IA).
- **Proposta Exata de Refatoração:**
  1. Criar função de sanitização XML/SVG no backend antes da persistência:
     - Remover tags `<script>`, elementos `<foreignObject>` não auditados e qualquer atributo iniciado com `on` (`onload`, `onclick`, `onerror`).
     - Descartar URIs contendo esquemas `javascript:` ou `data:text/html`.
  2. No endpoint `GET /media/images/{filename}`, injetar cabeçalho de resposta:
     - `Content-Security-Policy: default-src 'none'; style-src 'unsafe-inline'`
     - `X-Content-Type-Options: nosniff`.

---

### [SEC-06] Prevenção de Vazamento de Secrets e Stack Traces em Erros Globais
- **Localização:** [`backend/app/main.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/main.py) e handlers de exceção.
- **Problema:** Exceções não tratadas podem vazar detalhes de conexão com PostgreSQL, queries com parâmetros sensíveis ou caminhos absolutos do sistema operacional Windows/Linux caso o modo de depuração ou o manipulador padrão do FastAPI processe o erro.
- **Risco:** **Médio** (Vazamento de informações de infraestrutura e variáveis sensíveis).
- **Proposta Exata de Refatoração:**
  1. Adicionar um exception handler global para `Exception` em `main.py`.
  2. Gerar um identificador único de erro (`error_id = uuid.uuid4().hex[:8]`).
  3. Registrar o traceback completo exclusivamente nos logs internos com nível `logger.error`.
  4. Retornar resposta HTTP 500 neutra ao cliente: `{"detail": "Erro interno do servidor", "error_id": error_id}`.

---

```
====================================================================================================
PILAR 2: PERFORMANCE E BANCO DE DADOS (Event Loop, Redis Pooling, pgvector e N+1)
====================================================================================================
```

### [PERF-01] Criação e Destruição de Conexões Redis por Requisição (`get_redis`)
- **Localização:** [`backend/app/core/redis.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/core/redis.py).
- **Problema:** Anteriormente, cada invocação da dependência `get_redis` criava uma nova instância de conexão via `aioredis.from_url(...)` e a fechava com `await client.aclose()`. Sob tráfego concorrente (múltiplas requisições de áudio TTS, validações de token e chat), o overhead de handshake TCP e a exaustão de file descriptors prejudicam severamente o throughput.
- **Risco:** **Alto** (Gargalo de latência e possibilidade de esgotamento de portas TCP sob carga).
- **Proposta Exata de Refatoração:**
  1. Instanciar um pool de conexões único e global `aioredis.ConnectionPool.from_url` gerenciado pelo ciclo de vida da aplicação (`lifespan` em `main.py`).
  2. Implementar vinculação segura ao event loop ativo (`asyncio.get_running_loop()`), permitindo reaproveitamento estático em testes assíncronos e execuções concorrentes.
  3. Prover função de dependência `get_redis` que instancia clientes leves atrelados ao pool (`aioredis.Redis(connection_pool=pool)`), sem abrir/fechar conexões TCP a cada rota.
  4. Encerrar graciosamente o pool no desligamento do servidor (`await pool.disconnect()`).

---

### [PERF-02] I/O de Disco Síncrono Bloqueando o Event Loop Principal do Python
- **Localização:**
  - [`backend/app/services/tts.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/services/tts.py) (`file_path.read_bytes()`, `file_path.write_bytes()`);
  - [`backend/app/api/v1/endpoints/media.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/api/v1/endpoints/media.py) (`file_path.read_bytes()`);
  - [`backend/app/agent/illustrator.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/agent/illustrator.py) (`image_path.write_text()`);
  - Síntese de áudio PCM sintético (`_generate_synthetic_fallback_audio`): loop numérico intensivo executado na thread do event loop.
- **Problema:** Em rotas assíncronas (`async def`), qualquer operação de leitura ou escrita direta em disco e qualquer computação síncrona pesada travam a thread principal do asyncio. Enquanto o disco ou o processador processam o áudio, nenhuma outra requisição assíncrona é atendida.
- **Risco:** **Alto** (Picos desproporcionais de latência e colapso da capacidade assíncrona da API).
- **Proposta Exata de Refatoração:**
  1. No streaming de arquivos estáticos (`GET /media/audio/{hash}` e `GET /media/images/{name}`), utilizar `FileResponse(file_path)` do Starlette, que lê o arquivo em blocos em thread pool dedicada sem bloquear o event loop.
  2. No salvamento de arquivos de áudio em disco e na sintetização acústica, delegar as tarefas para o pool de threads do asyncio com `await asyncio.to_thread(...)` ou `await anyio.to_thread.run_sync(...)`.
  3. No agente Ilustrador, encapsular a gravação de arquivos SVG em disco dentro de `asyncio.to_thread(image_path.write_text, svg_code, encoding="utf-8")`.

---

### [PERF-03] Dimensionamento do Índice HNSW do pgvector e Índice B-Tree de Chave Estrangeira
- **Localização:**
  - [`backend/app/models/rag.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/models/rag.py) (`DocumentChunk.document_id`);
  - [`backend/app/rag/retriever.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/rag/retriever.py);
  - Migrações Alembic da Biblioteca de Alexandria.
- **Problema:**
  - Em versões anteriores, a chave estrangeira `document_chunks.document_id` não possuía índice B-Tree individual garantido, resultando em *sequential scans* ao fazer `JOIN` ou exclusões em cascata com `library_documents`.
  - O índice vetorial HNSW foi configurado com parâmetros padrão conservadores `(m = 16, ef_construction = 64)`.
  - Na busca por similaridade semântica em `retriever.py`, a sessão do banco não configurava explicitamente o parâmetro de busca `hnsw.ef_search`, utilizando o default do Postgres (`40`), o que reduz a taxa de recuperação (*recall*) para textos clássicos em latim com vocabulário esparso.
- **Risco:** **Médio** (Perda gradual de precisão no RAG e lentidão de consultas à medida que o acervo de Alexandria cresce).
- **Proposta Exata de Refatoração:**
  1. Garantir migração Alembic criando índice B-Tree em `document_chunks(document_id)`.
  2. Em `retriever.py`, executar antes da consulta vetorial:
     `await db.execute(text("SET LOCAL hnsw.ef_search = 100;"))`
     Isso eleva o *recall* acima de 95% mantendo a latência na faixa de sub-milissegundos.
  3. Documentar recomendação operacional de infraestrutura: em ambientes de produção com grande volume de dados (>100k fragmentos), ajustar `m=24` e `ef_construction=128`, configurando `SET maintenance_work_mem = '512MB'` durante a recriação do índice HNSW.

---

### [PERF-04] Consultas Repetitivas e Redundantes ao Catálogo de Badges
- **Localização:** [`backend/app/services/gamification.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/services/gamification.py) (`evaluate_and_award_badges`).
- **Problema:** A cada término de lição ou submissão de exercício com nota máxima, a rotina de avaliação consulta a tabela inteira `badges` (`SELECT * FROM badges`). Como os badges do Senado Romano são dados canônicos estáticos do curso, reconsultar o banco relacional repetidamente gera tráfego e latência desnecessários.
- **Risco:** **Baixo-Médio** (Sobrecarga de round-trips ao PostgreSQL em eventos frequentes dos alunos).
- **Proposta Exata de Refatoração:**
  1. Criar um cache em memória com TTL (ex: 3600 segundos / 1 hora) com fallback de carregamento assíncrono para o catálogo de badges.
  2. Utilizar invalidação explícita de cache caso um endpoint administrativo atualize os critérios ou adicione insígnias.

---

### [PERF-05] Auditoria de Queries N+1 no SQLAlchemy & Recarregamento de Progresso
- **Localização:**
  - [`backend/app/api/v1/endpoints/lessons.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/api/v1/endpoints/lessons.py) (`list_course_modules` e `complete_lesson`);
  - [`backend/app/api/v1/endpoints/badges.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/api/v1/endpoints/badges.py) (`list_user_badges`).
- **Diagnóstico da Auditoria:**
  1. *Eager Loading em Módulos*: Em `list_course_modules`, o uso de `selectinload(CourseModule.lessons)` foi confirmado como correto para evitar N+1 ao agrupar lições por módulo.
  2. *Query Redundante em `complete_lesson`*: Após computar e comitar o progresso do aluno, o endpoint invocava novamente a função `_get_or_create_user_progress(db, current_user.id)`, que disparava uma query completa adicional. A solução otimizada deve apenas recarregar as relações atualizadas na mesma sessão via `await db.refresh(progress, ["current_module", "current_lesson"])`.
  3. *Carregamento Eager em Insígnias*: Na listagem de insígnias conquistadas pelo aluno (`/badges/my`), certificar que a query execute `options(selectinload(UserBadge.badge))` para carregar os metadados dos badges em uma única query otimizada com cláusula `IN (...)`, eliminando qualquer carregamento tardio por linha.
- **Risco:** **Baixo-Médio** (I/O desnecessário no banco em endpoints de navegação primária).
- **Proposta Exata de Refatoração:**
  1. Refatorar `complete_lesson` eliminando o re-fetch redundante e aplicando `refresh(progress, ["current_module", "current_lesson"])`.
  2. Padronizar `selectinload` em todas as relações um-para-muitos e muitos-para-um dos endpoints do aluno.

---

### [PERF-06] Bloqueio do Event Loop por Criptografia CPU-Bound de Senhas (`bcrypt`)
- **Localização:** [`backend/app/core/security.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/core/security.py) (`verify_password`, `get_password_hash`) e [`backend/app/api/v1/endpoints/auth.py`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/app/api/v1/endpoints/auth.py).
- **Problema:** O algoritmo de derivação de chave Bcrypt é propositalmente custoso em termos de CPU (fator de custo 12, levando ~200 a 300ms por operação). Quando `verify_password` ou `get_password_hash` são chamados diretamente dentro das rotas assíncronas `async def login` ou `async def register`, a thread principal do asyncio é congelada durante o cálculo. Se múltiplos usuários tentarem autenticar simultaneamente, a API deixa de processar quaisquer outras requisições concorrentes.
- **Risco:** **Alto** (Spikes de latência na API e degradação súbita sob rajadas de login).
- **Proposta Exata de Refatoração:**
  1. Encapsular as operações de hash e checagem de senha em adaptadores assíncronos:
     ```python
     async def verify_password_async(plain: str, hashed: str) -> bool:
         return await asyncio.to_thread(verify_password, plain, hashed)

     async def get_password_hash_async(password: str) -> str:
         return await asyncio.to_thread(get_password_hash, password)
     ```
  2. Substituir as chamadas síncronas em `auth.py` pelas versões offloaded em thread pool.

---

```
====================================================================================================
PILAR 3: QUALIDADE DE CÓDIGO E CI/CD (Ruff, Mypy e GitHub Actions)
====================================================================================================
```

### [QUAL-01] Ausência de Testes e Validação do Frontend no GitHub Actions
- **Localização:** [`.github/workflows/ci.yml`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/.github/workflows/ci.yml).
- **Problema:** O workflow continha exclusivamente o job de backend (`backend-quality-and-tests`). Alterações na camada de interface (TypeScript/React) não eram submetidas a checagem de tipos estrita (`tsc --noEmit`) nem ao build do Vite no CI. Erros de compilação ou dependências ausentes no frontend só seriam descobertos no momento do deploy.
- **Risco:** **Alto** (Possibilidade de merge e deploy de frontend quebrado em branch principal).
- **Proposta Exata de Refatoração:**
  1. Adicionar o job `frontend-quality-and-build` em `.github/workflows/ci.yml`:
     - Configuração de Node.js 20 com cache automático de dependências via `cache: "npm"` apontando para `frontend/package-lock.json`;
     - Execução determinística de `npm ci` no diretório `frontend`;
     - Execução de `npm run build` para garantir validação de tipos TypeScript e empacotamento completo sem erros.

---

### [QUAL-02] Escopo Incompleto do Mypy e Monitoramento de Cobertura com Pytest
- **Localização:** [`.github/workflows/ci.yml`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/.github/workflows/ci.yml) e [`backend/pyproject.toml`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/pyproject.toml).
- **Problema:**
  - O comando no CI executava `mypy app`, ignorando a suíte de testes (`tests/`), permitindo que tipos incorretos ou mocks mal tipados se acumulassem nos testes.
  - Não havia métrica automatizada de cobertura de código no CI (`pytest-cov`), permitindo que novos endpoints fossem adicionados sem testes unitários correspondentes.
- **Risco:** **Médio** (Dívida técnica silenciosa na suíte de testes e regressões funcionais).
- **Proposta Exata de Refatoração:**
  1. Atualizar o comando do CI para `mypy app tests`.
  2. Configurar `pytest-cov` na suíte de testes com parâmetro `--cov=app --cov-report=term-missing`.
  3. Estabelecer meta de barreira de cobertura mínima de 80% do código de negócio.

---

### [QUAL-03] Enrijecimento das Regras de Linting do Ruff
- **Localização:** [`backend/pyproject.toml`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/backend/pyproject.toml).
- **Problema:** O conjunto de regras inicial incluía apenas regras básicas (`E, W, F, I, B, C4, UP, SIM`). Faltavam detectores especializados de falhas assíncronas, segurança de código, instruções de debug esquecidas e código comentado.
- **Risco:** **Médio** (Código legado acumulado, prints acidentais em produção e armadilhas no event loop).
- **Proposta Exata de Refatoração:**
  1. Adicionar ao array `select` do `[tool.ruff.lint]`:
     - `"S"`: `flake8-bandit` (análise estática de vulnerabilidades de segurança, injeções e senhas);
     - `"ASYNC"`: `flake8-async` (detecta bloqueios e padrões incorretos em rotinas assíncronas);
     - `"T20"`: `flake8-print` (proíbe terminantemente instruções `print()` em favor do módulo `logging`);
     - `"ERA"`: `eradicate` (detecta e força a remoção de blocos de código comentados);
     - `"RUF"`: regras nativas de otimização do ecossistema Ruff.
  2. Ajustar regras de ignore conscientes para FastAPI: `B008` (para `Depends()`) e `S104` (binding local em desenvolvimento).

---

### [QUAL-04] Resiliência dos Contêineres de Serviço no CI (Eliminação de Falsos Positivos)
- **Localização:** [`.github/workflows/ci.yml`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/.github/workflows/ci.yml).
- **Problema:** Serviços de contêiner (PostgreSQL/pgvector e Redis) podem demorar alguns segundos para inicializar no GitHub Actions. Se o job iniciar os testes antes que o socket do Postgres ou do Redis esteja aceitando conexões, o pipeline falha com falso positivo.
- **Risco:** **Médio** (Pipelines instáveis com falhas intermitentes no CI).
- **Proposta Exata de Refatoração:**
  1. Configurar `options` com health checks nativos nos serviços do workflow:
     - PostgreSQL: `--health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5`
     - Redis: `--health-cmd "redis-cli ping" --health-interval 10s --health-timeout 5s --health-retries 5`
  2. Isso garante que o runner do GitHub Actions só inicie a execução do backend após a infraestrutura estar 100% saudável.

---

```
====================================================================================================
PILAR 4: FRONTEND E UX (Code Splitting, Bundle Size e Re-renders)
====================================================================================================
```

### [FRONT-01] Bundle Monolítico sem Code-Splitting / Lazy Loading
- **Localização:** [`frontend/src/App.tsx`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/frontend/src/App.tsx) e [`frontend/vite.config.ts`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/frontend/vite.config.ts).
- **Problema:** Imports estáticos sincronizados carregavam todo o ecossistema de uma só vez. Um visitante não autenticado que acessa apenas a tela de login era forçado a baixar todo o código da `ClassroomPage` (com centenas de linhas de lógica de avaliação, flashcards 3D, ícones e componentes do Senado). O bundle inicial gerado em um único chunk JS ultrapassava os limites recomendados de performance móvel.
- **Risco:** **Médio** (Tempo de carregamento inicial elevado no primeiro acesso em conexões móveis 3G/4G e no Safari iOS).
- **Proposta Exata de Refatoração:**
  1. Implementar divisão de código dinâmica com `React.lazy()` e `<Suspense>` em `App.tsx` para as rotas:
     - `LoginPage`, `DashboardPage`, `ClassroomPage`, `ProfilePage`.
  2. Criar componente visual de fallback (`PageFallback`) com estética romana condizente com a identidade visual do projeto durante o carregamento dos chunks.
  3. No [`frontend/vite.config.ts`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/frontend/vite.config.ts), configurar `build.rollupOptions.output.manualChunks` segregando:
     - `vendor-react`: `react`, `react-dom`;
     - `vendor-ui`: `lucide-react`;
     - `vendor-http`: `axios`.

---

### [FRONT-02] Instanciação de Objetos Literais em Provedores de Contexto do React
- **Localização:**
  - [`frontend/src/context/AuthContext.tsx`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/frontend/src/context/AuthContext.tsx);
  - [`frontend/src/context/ProgressContext.tsx`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/frontend/src/context/ProgressContext.tsx).
- **Problema:** A propriedade `value={{ ... }}` nos provedores `AuthContext.Provider` e `ProgressContext.Provider` instanciava novos objetos literais a cada ciclo de renderização. Como a referência de memória mudava continuamente, todos os componentes consumidores da árvore eram forçados a re-renderizar desnecessariamente, mesmo quando os valores internos não haviam mudado.
- **Risco:** **Baixo-Médio** (Desperdício de ciclos de CPU e perda da meta de 60fps em dispositivos móveis durante digitação ou animações).
- **Proposta Exata de Refatoração:**
  1. Embalar o valor dos contextos com `useMemo` atrelado às dependências reais do estado.
  2. Estabilizar todas as funções manipuladoras (`login`, `logout`, `fetchProgress`, `completeLessonAction`, etc.) com `useCallback`.

---

### [FRONT-03] Robustez e Gestão de Concorrência na Fila do Interceptor Axios
- **Localização:** [`frontend/src/api/client.ts`](file:///c:/Users/mbpap/OneDrive/Documents/Rodrigo/LATIN_CLASS/frontend/src/api/client.ts).
- **Problema:**
  - *Cancelamento não tratado*: Se uma requisição enfileirada na fila de renovação (`failedQueue`) for cancelada pelo chamador (via `AbortSignal` por desmontagem de componente React), o reenvio subsequente disparava sobre a requisição abortada, gerando rejeições de promessa silenciosas ou exceções não capturadas.
  - *Bloqueio por Timeout de Rede*: Se a rotação `/auth/refresh` entrasse em um estado de congelamento por instabilidade de rede (ex: transição Wi-Fi/4G no celular), a flag `isRefreshing = true` permanecia travada, bloqueando todas as requisições subsequentes do usuário sem efetuar logout limpo.
  - *Sincronização Multi-Aba*: Se o usuário estivesse com múltiplas abas abertas e fizesse logout em uma delas, as demais continuavam com estado dessincronizado até que um erro 401 ocorresse.
- **Risco:** **Médio** (Travamento da interface em oscilações de rede ou reenvio de requisições canceladas).
- **Proposta Exata de Refatoração:**
  1. Verificar `originalRequest.signal?.aborted` antes de reenfileirar e disparar a requisição renovada.
  2. Adicionar timeout rígido de 10 segundos (`timeout: 10000`) na chamada de `/auth/refresh` com bloco `finally` garantindo reset incondicional de `isRefreshing = false`.
  3. Adicionar listener global para evento de sincronização entre abas:
     ```typescript
     window.addEventListener('storage', (event: StorageEvent) => {
       if (event.key === 'latium_refresh_token' && !event.newValue) {
         setAccessToken(null);
         if (onUnauthorizedCallback) onUnauthorizedCallback();
       }
     });
     ```

---

## 3. Matriz de Priorização e Plano de Ação

A execução da Fase 7 é recomendada em **4 ondas cronológicas**, organizadas estritamente pela criticidade, impacto na estabilidade e segurança da plataforma:

| Prioridade | ID | Descrição do Débito Técnico | Esforço | Impacto | Justificativa de Engenharia |
|---|---|---|---|---|---|
| **P0 (Crítico)** | `PERF-01` | Pool de Conexões Persistente no Redis | Médio | Altíssimo | Elimina o esgotamento de portas/conexões sob carga concorrente |
| **P0 (Crítico)** | `PERF-02` | I/O de Disco e Áudio PCM Não-Bloqueante | Médio | Altíssimo | Impede que o Event Loop trave durante geração de TTS ou ilustrações |
| **P0 (Crítico)** | `QUAL-01` | Inclusão de Job de Frontend e `mypy tests` no CI | Baixo | Altíssimo | Garante que código quebrado de React/TS nunca chegue à produção |
| **P0 (Crítico)** | `SEC-04` | Validador Pydantic para `SECRET_KEY` em Produção | Baixo | Altíssimo | Previne brecha fatal de segurança criptográfica em ambiente produtivo |
| **P1 (Alto)** | `SEC-01` | Rate Limiting no Redis para `/login` e `/register` | Médio | Alto | Bloqueia ataques automatizados de força bruta e DoS |
| **P1 (Alto)** | `PERF-06` | Offload de Hash Bcrypt para Threadpool | Baixo | Alto | Elimina congelamento do asyncio por computação intensiva de CPU |
| **P1 (Alto)** | `FRONT-01` | Code Splitting (`React.lazy`) e `manualChunks` | Médio | Alto | Otimiza drasticamente o tempo de carregamento no Safari iOS |
| **P1 (Alto)** | `SEC-05` | Sanitização Defensiva de SVGs contra XSS | Baixo | Alto | Blindagem contra injeção em ilustrações geradas por IA |
| **P2 (Médio)** | `SEC-03` | Middleware de Security Headers HTTP | Baixo | Médio | Proteção contra Clickjacking e MIME-sniffing |
| **P2 (Médio)** | `PERF-03` | Índice B-Tree em FK de Chunks e Ajuste `ef_search` | Baixo | Médio | Otimiza recall do RAG e previne sequential scans com escala |
| **P2 (Médio)** | `QUAL-03` | Enrijecimento das Regras do Ruff (`S`, `ASYNC`, `T20`, `ERA`, `RUF`) | Baixo | Médio | Padronização de qualidade e prevenção estática de bugs |
| **P2 (Médio)** | `FRONT-03` | Gestão Resiliente da Fila do Interceptor Axios | Médio | Médio | Evita travamento da interface em variações de rede e cancelamentos |
| **P2 (Médio)** | `QUAL-04` | Health Checks em Serviços de Contêiner do CI | Baixo | Médio | Elimina falsos positivos intermitentes em pipelines |
| **P3 (Baixo)** | `FRONT-02` | Estabilização de Contextos com `useMemo`/`useCallback` | Baixo | Baixo-Médio | Otimiza renderizações redundantes no React |
| **P3 (Baixo)** | `PERF-04` | Cache em Memória para Catálogo de Badges | Baixo | Baixo | Reduz round-trips estáticos ao PostgreSQL |
| **P3 (Baixo)** | `PERF-05` | Eliminação de Queries Redundantes no Progresso | Baixo | Baixo | Otimiza término de lições substituindo queries por `db.refresh` |
| **P3 (Baixo)** | `SEC-02` | Detecção de Reuso de Refresh Token no Redis | Médio | Médio | Eleva a maturidade contra roubo persistente de sessão |
| **P3 (Baixo)** | `SEC-06` | Handler Global de Erro com Sanitização de Stack Trace | Baixo | Baixo-Médio | Previne vazamento de informações de infraestrutura |

---

## 4. Próximos Passos & Recomendação de Execução

1. **Revisão pelo Tech Lead:**
   - Avaliar a matriz de priorização e validar se as 4 ondas cronológicas cobrem as metas estratégicas para a Fase 7.
2. **Execução Controlada em Ondas:**
   - **Onda 1 (P0):** Resolver gargalos de estabilidade e CI (`PERF-01`, `PERF-02`, `QUAL-01`, `SEC-04`).
   - **Onda 2 (P1):** Implementar defesas primárias e performance de interface (`SEC-01`, `PERF-06`, `FRONT-01`, `SEC-05`).
   - **Onda 3 (P2):** Aplicar segurança de headers, índices vetoriais, enrijecimento do linter e interceptor Axios (`SEC-03`, `PERF-03`, `QUAL-03`, `FRONT-03`, `QUAL-04`).
   - **Onda 4 (P3):** Polimento de re-renders no frontend, cache de gamificação e refinamentos residuais (`FRONT-02`, `PERF-04`, `PERF-05`, `SEC-02`, `SEC-06`).
3. **Verificação de Regressão:**
   - Executar a suíte de 40+ testes com cobertura, validação Mypy estrita em `app` e `tests`, linting do Ruff e build do frontend após cada onda.

---

> 🛑 **REGRA DE PARADA RESPEITADA (SYSTEM HALT):**  
> Nenhuma modificação em código-fonte foi realizada nesta intervenção. A auditoria técnica foi concluída com sucesso e consolidada integralmente em `Audit_Plan_Fase7.md`.  
> O agente encontra-se estritamente em pausa, aguardando a revisão e a autorização explícita do Tech Lead para prosseguir com a execução.

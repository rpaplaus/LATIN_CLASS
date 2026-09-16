# 🏛️ Latium AI - Intelligent Latin Tutoring Platform

Plataforma inteligente e mobile-first para o ensino e prática da língua latina, orientada por agentes de IA e fundamentada em materiais didáticos de referência.

---

## 📐 Arquitetura & Stack Tecnológica

### Backend & API
- **FastAPI**: Framework web moderno, assíncrono e tipado.
- **Python 3.12**: Tipagem estática rigorosa com verificação via **Mypy (strict)**.
- **SQLAlchemy 2.0 (Async)** + **asyncpg**: Operações assíncronas no banco de dados.
- **PostgreSQL 16** com extensão **pgvector**: Armazenamento relacional e suporte nativo a embeddings para futuras fases de RAG.
- **Redis 7 (Alpine)**: Cache de sessão, rate limiting e memória de curto prazo.
- **Alembic**: Migrações assíncronas versionadas de esquema.
- **Autenticação JWT**: Padrão OAuth2 Password Flow com hash bcrypt.

### Qualidade & CI/CD
- **Ruff**: Linter e formatador de altíssima performance.
- **Mypy**: Checagem estática de tipos em modo estrito.
- **Pytest + pytest-asyncio**: Suite de testes assíncronos automatizados.
- **Docker & Docker Compose**: Paridade de ambiente e isolamento de serviços.

---

## 🚀 Como Executar

### 1. Pré-requisitos
- Docker & Docker Compose
- Python 3.12+ (para execução local opcional)

### 2. Executando com Docker Compose (Recomendado)
```bash
# 1. Copiar variáveis de ambiente
cp .env.example .env

# 2. Subir todos os serviços (PostgreSQL, Redis e Backend)
docker compose up -d

# 3. Executar migrações do banco
docker compose exec backend alembic upgrade head
```

- **API Docs (Swagger UI)**: [http://localhost:8001/docs](http://localhost:8001/docs)
- **Health Check**: [http://localhost:8001/api/v1/health](http://localhost:8001/api/v1/health)

### 3. Execução Local para Desenvolvimento (Host)
```bash
# 1. Subir apenas os serviços de banco e cache
docker compose up -d postgres redis

# 2. Criar e ativar ambiente virtual
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 3. Instalar dependências em modo editável com ferramentas de desenvolvimento
pip install -e "./backend[dev]"

# 4. Rodar as migrações
cd backend
alembic upgrade head

# 5. Iniciar o servidor de desenvolvimento
uvicorn app.main:app --reload --port 8000
```

---

## 🧪 Qualidade de Código e Testes

Execute a partir do diretório `backend/`:

```bash
# Linting com Ruff
ruff check app tests

# Verificação de Formatação com Ruff
ruff format --check app tests

# Checagem estática de tipos com Mypy (Strict)
mypy app

# Execução da suite de testes assíncronos
pytest -v
```

---

## 📡 Endpoints da API (Fase 1)

| Método | Rota | Descrição | Acesso |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Healthcheck de integridade da API, PostgreSQL e Redis | Público |
| `POST` | `/api/v1/auth/register` | Cadastro de novo aluno (retorna dados sem hash de senha) | Público |
| `POST` | `/api/v1/auth/login` | Login via formulário OAuth2 (`application/x-www-form-urlencoded`) | Público |
| `GET` | `/api/v1/auth/me` | Retorna o perfil do usuário autenticado via Bearer Token | Aluno Autenticado |
| `PATCH` | `/api/v1/users/me` | Atualiza dados cadastrais (nome, senha) do aluno logado | Aluno Autenticado |
| `GET` | `/api/v1/users/` | Lista usuários da plataforma | Apenas Superusuários |

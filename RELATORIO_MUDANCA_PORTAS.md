# Relatório de Reconfiguração de Portas — Latin Class (Latium AI)

## 1. Contexto e Objetivo

Na máquina de desenvolvimento hospedeira, outros projetos e serviços já estavam em execução ocupando as seguintes portas de rede:
- **Porta 3000** (serviço web / frontend de outro projeto)
- **Porta 5173** (servidor Vite padrão de outro projeto)
- **Porta 8000** (serviço backend / API de outro projeto)

O objetivo desta intervenção foi **reconfigurar o projeto Latin Class para desvincular completamente o uso das portas `3000`, `5173` e `8000`**, tanto no ambiente conteinerizado (**Docker / Docker Compose**) quanto no desenvolvimento local no host (**Vite / Uvicorn**), garantindo compatibilidade total e eliminando colisões de portas.

---

## 2. Mapeamento de Portas: Antes vs. Depois

| Componente | Função | Porta Antiga | Nova Porta Escolhida | Justificativa |
| :--- | :--- | :--- | :--- | :--- |
| **Frontend (Host / Docker)** | Acesso à interface web no navegador | `3000` | **`3001`** | Porta livre na máquina, padrão imediato seguinte para aplicações web front-end. |
| **Frontend (Vite Dev Server)** | Servidor de desenvolvimento / HMR local e interno do container | `5173` | **`5174`** | Porta livre na máquina, padrão imediato do ecossistema Vite ao encontrar `5173` ocupada. |
| **Backend (FastAPI / Uvicorn)** | API REST e Documentação Swagger/ReDoc | `8000` / `8001` (espelhada) | **`8001`** | A porta `8001` já estava reservada nos scripts e documentação do projeto, mas a porta `8000` ainda estava exposta e vinculada no Docker (`8000:8000`), no Dockerfile e nas instruções locais. Removeu-se completamente a `8000`, padronizando na **`8001`**. |

> [!NOTE]
> As portas de infraestrutura de banco de dados (`PostgreSQL: 5433` e `Redis: 6380`) foram mantidas inalteradas, pois já utilizavam portas customizadas não colidentes com os padrões `5432` e `6379`.

---

## 3. Arquivos Modificados e Detalhamento das Alterações

### 1. [`.env`](file:///c:/Users/rpapl/.gemini/antigravity-ide/scratch/LATIN_CLASS/.env)
- **Adicionado:** Variáveis explícitas de controle de portas:
  ```env
  FRONTEND_PORT=3001
  BACKEND_PORT=8001
  ```
- **Atualizado:** `CORS_ORIGINS` para remover `3000`, `5173` e `8000`, incluindo as novas portas `3001` e `5174`:
  ```env
  CORS_ORIGINS=["http://localhost:3001","http://127.0.0.1:3001","http://localhost:5174","http://127.0.0.1:5174","http://localhost:8001","http://127.0.0.1:8001"]
  ```

### 2. [`.env.example`](file:///c:/Users/rpapl/.gemini/antigravity-ide/scratch/LATIN_CLASS/.env.example)
- **Sincronizado:** Adicionadas as variáveis `FRONTEND_PORT=3001` e `BACKEND_PORT=8001` e atualizada a lista de exemplos de `CORS_ORIGINS` para referência da equipe.

### 3. [`docker-compose.yml`](file:///c:/Users/rpapl/.gemini/antigravity-ide/scratch/LATIN_CLASS/docker-compose.yml)
- **Backend:**
  - **Mapeamento de Portas:** Removido `- "8000:8000"`. Atualizado para `"${BACKEND_PORT:-8001}:8001"`.
  - **Comando do container:** Alterado `--port 8000` para `--port 8001`.
  - **CORS_ORIGINS:** Atualizado para incluir as portas `3001`, `5174` e `8001`.
- **Frontend:**
  - **Mapeamento de Portas:** Atualizado de `"${FRONTEND_PORT:-3000}:5173"` para `"${FRONTEND_PORT:-3001}:5174"`.
  - **Variáveis de Ambiente:** Adicionada `VITE_BACKEND_URL=http://backend:8001` para roteamento interno correto dentro da rede Docker.
  - **Comando do container:** Alterado de `--port 5173` para `--port 5174`.

### 4. [`frontend/vite.config.ts`](file:///c:/Users/rpapl/.gemini/antigravity-ide/scratch/LATIN_CLASS/frontend/vite.config.ts)
- **Porta do Servidor:** Modificada de `5173` para `5174`.
- **Proxy `/api`:** Atualizado fallback padrão de target de `http://backend:8000` para `http://localhost:8001` (permitindo que o comando `npm run dev` local no host acesse a API FastAPI na porta `8001` sem necessitar de configurações manuais adicionais).

### 5. [`frontend/Dockerfile`](file:///c:/Users/rpapl/.gemini/antigravity-ide/scratch/LATIN_CLASS/frontend/Dockerfile)
- **EXPOSE:** Atualizado de `5173` para `5174`.
- **CMD:** Atualizado para executar `npm run dev -- --host 0.0.0.0 --port 5174`.

### 6. [`backend/Dockerfile`](file:///c:/Users/rpapl/.gemini/antigravity-ide/scratch/LATIN_CLASS/backend/Dockerfile)
- **EXPOSE:** Atualizado de `8000` para `8001`.
- **CMD:** Atualizado para `uvicorn app.main:app --host 0.0.0.0 --port 8001`.

### 7. [`backend/app/core/config.py`](file:///c:/Users/rpapl/.gemini/antigravity-ide/scratch/LATIN_CLASS/backend/app/core/config.py)
- **Lista padrão de `CORS_ORIGINS`:** Substituídas as origens que utilizavam `3000`, `5173` e `8000` pelas novas portas:
  - `http://localhost:3001` e `http://127.0.0.1:3001` (Frontend via Docker)
  - `http://localhost:5174` e `http://127.0.0.1:5174` (Frontend via Vite local)
  - `http://localhost:8001` e `http://127.0.0.1:8001` (Backend API)

### 8. [`README.md`](file:///c:/Users/rpapl/.gemini/antigravity-ide/scratch/LATIN_CLASS/README.md)
- **Diagrama de Arquitetura Mermaid:** Atualizado de `http://localhost:3000` para `http://localhost:3001`.
- **URLs de Acesso:** Atualizadas as URLs do frontend para `http://localhost:3001` (ou `5174` em dev local) e backend para `http://localhost:8001`.
- **Guia de Execução Local:** Atualizado o comando de inicialização manual do backend para `uvicorn app.main:app --reload --port 8001`.

---

## 4. Novas URLs de Acesso

Com as alterações aplicadas, os serviços estão disponíveis nos seguintes endereços:

- 🏛️ **Frontend (Aplicação Web via Docker):** [http://localhost:3001](http://localhost:3001)
- ⚡ **Frontend (Desenvolvimento Local via `npm run dev`):** [http://localhost:5174](http://localhost:5174)
- ⚙️ **Backend API (FastAPI):** [http://localhost:8001](http://localhost:8001)
- 📖 **Documentação Swagger UI:** [http://localhost:8001/docs](http://localhost:8001/docs)
- 📚 **Documentação ReDoc:** [http://localhost:8001/redoc](http://localhost:8001/redoc)
- 🩺 **Healthcheck de Serviços:** [http://localhost:8001/api/v1/health](http://localhost:8001/api/v1/health)

---

## 5. Como Executar o Projeto Agora

### Opção A: Execução via Docker Compose (Recomendada)
```bash
# Subir toda a infraestrutura e containers
docker compose up -d --build
```
Acesse o sistema em: **`http://localhost:3001`**.

### Opção B: Execução Local no Host (Modo Híbrido)
1. **Subir apenas banco de dados e cache no Docker:**
   ```bash
   docker compose up -d postgres redis
   ```
2. **Iniciar o Backend:**
   ```bash
   cd backend
   uvicorn app.main:app --reload --port 8001
   ```
3. **Iniciar o Frontend:**
   ```bash
   cd frontend
   npm run dev
   ```
   Acesse em: **`http://localhost:5174`** (com proxy automático redirecionando `/api` para `http://localhost:8001`).

---

## 6. Verificações e Auditoria Realizadas

1. **Varredura Global de Código:**
   - Realizada busca recursiva em todos os arquivos de configuração, scripts, código-fonte e documentação. Confirmou-se que não resta nenhuma ocorrência das portas `3000`, `5173` ou `8000`.
2. **Validação do Docker Compose:**
   - Executado `docker compose config` com sucesso. O compilador validou a sintaxe, as variáveis de ambiente e o roteamento das novas portas (`3001:5174` para frontend e `8001:8001` para backend).
3. **Disponibilidade das Portas no Sistema:**
   - Confirmado via inspeção de sockets TCP no Windows que as portas `3001`, `5174` e `8001` estavam completamente livres e disponíveis para uso imediato.

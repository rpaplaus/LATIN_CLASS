#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

echo "Subindo todos os containers do Latin Class em background..."
docker compose up -d

echo ""
echo "Aguardando o banco de dados e backend iniciarem..."
sleep 5

echo "Executando Alembic dentro do container backend..."
docker compose exec backend alembic upgrade head || true

echo ""
echo "Tudo pronto! O Latin Class está rodando via Docker."
echo "Frontend: http://localhost:3001"
echo "Backend:  http://localhost:8001"


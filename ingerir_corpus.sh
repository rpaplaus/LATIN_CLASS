#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

echo "Ingerindo o corpus clássico da Biblioteca de Alexandria no pgvector..."
docker compose exec backend python scripts/ingest_corpus.py


@echo off
cd /d "%~dp0"

echo Ingerindo o corpus classico da Biblioteca de Alexandria no pgvector...
docker compose exec backend python scripts/ingest_corpus.py
pause


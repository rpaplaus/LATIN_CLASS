import asyncio
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.database import async_session_factory
from app.rag.ingestion import ingest_corpus_seed


async def main() -> None:
    print("=============================================================")
    print("[ALEXANDRIA] INGESTAO DA BIBLIOTECA DE ALEXANDRIA (RAG)")
    print("=============================================================")
    print("Conectando ao PostgreSQL e processando obras canonicas...")

    async with async_session_factory() as session:
        try:
            total = await ingest_corpus_seed(session)
            print(f"[OK] Ingestao concluida com sucesso! Total de fragmentos indexados: {total}")
        except Exception as exc:
            print(f"[ERRO] Falha durante a ingestao do corpus: {exc}")
            raise


if __name__ == "__main__":
    asyncio.run(main())

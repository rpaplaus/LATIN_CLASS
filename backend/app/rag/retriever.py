import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rag import DocumentChunk, LibraryDocument
from app.rag.embeddings import get_embedding

logger = logging.getLogger(__name__)


async def search_library_chunks(
    db: AsyncSession,
    query: str,
    top_k: int = 3,
    author_filter: str | None = None,
    era_filter: str | None = None,
) -> list[dict[str, Any]]:
    """Search Alexandria Latin Library using pgvector cosine distance on DocumentChunk embeddings."""
    query_vector = await get_embedding(query)

    stmt = select(DocumentChunk, LibraryDocument).join(
        LibraryDocument, DocumentChunk.document_id == LibraryDocument.id
    )

    if author_filter:
        stmt = stmt.where(LibraryDocument.author.ilike(f"%{author_filter.strip()}%"))

    if era_filter:
        stmt = stmt.where(LibraryDocument.era_category.ilike(f"%{era_filter.strip()}%"))

    # Order by cosine distance ascending (closest first)
    stmt = stmt.order_by(DocumentChunk.embedding.cosine_distance(query_vector)).limit(
        top_k
    )

    result = await db.execute(stmt)
    rows = result.all()

    formatted_results: list[dict[str, Any]] = []
    for chunk, doc in rows:
        formatted_results.append(
            {
                "chunk_id": str(chunk.id),
                "citation": chunk.citation,
                "content": chunk.content,
                "translation": chunk.translation,
                "author": doc.author,
                "title": doc.title,
                "era_category": doc.era_category,
                "metadata": chunk.metadata_ or {},
            }
        )

    logger.info(
        "Alexandria Library search for '%s' returned %d chunks",
        query,
        len(formatted_results),
    )
    return formatted_results


def format_chunks_for_context(chunks: list[dict[str, Any]]) -> str:
    """Format retrieved library chunks into a clean, humanistic context block for the Magister Latium."""
    if not chunks:
        return "Nenhum fragmento relevante encontrado na Biblioteca de Alexandria."

    formatted_blocks: list[str] = []
    for i, c in enumerate(chunks, start=1):
        block = (
            f"[{i}] {c['author']} — {c['title']} ({c['citation']})\n"
            f'Latim: "{c["content"]}"\n'
        )
        if c.get("translation"):
            block += f'Tradução / Notas: "{c["translation"]}"\n'
        formatted_blocks.append(block)

    return "\n".join(formatted_blocks)

import math

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.tools import search_latin_library
from app.models.rag import DocumentChunk, LibraryDocument
from app.rag.embeddings import (
    EMBEDDING_DIM,
    _deterministic_mock_embedding,
    get_embedding,
    get_embeddings_batch,
)
from app.rag.ingestion import ingest_corpus_seed
from app.rag.retriever import format_chunks_for_context, search_library_chunks


def test_deterministic_mock_embedding_properties() -> None:
    """Verify mock embedding generates 1536-dim, L2-normalized, deterministic vectors."""
    text1 = "Gallia est omnis divisa in partes tres."
    text2 = "Gallia est omnis divisa in partes tres."
    text3 = "O tempora, o mores!"

    vec1 = _deterministic_mock_embedding(text1)
    vec2 = _deterministic_mock_embedding(text2)
    vec3 = _deterministic_mock_embedding(text3)

    assert len(vec1) == EMBEDDING_DIM
    assert len(vec2) == EMBEDDING_DIM
    assert len(vec3) == EMBEDDING_DIM

    # Determinism
    assert vec1 == vec2
    assert vec1 != vec3

    # L2 norm must be approximately 1.0
    norm1 = math.sqrt(sum(x * x for x in vec1))
    norm3 = math.sqrt(sum(x * x for x in vec3))
    assert math.isclose(norm1, 1.0, rel_tol=1e-5)
    assert math.isclose(norm3, 1.0, rel_tol=1e-5)


@pytest.mark.asyncio
async def test_get_embedding_interface() -> None:
    """Verify get_embedding returns a valid 1536-dimensional vector."""
    vec = await get_embedding("Quo usque tandem abutere, Catilina, patientia nostra?")
    assert isinstance(vec, list)
    assert len(vec) == EMBEDDING_DIM
    assert all(isinstance(x, float) for x in vec)


@pytest.mark.asyncio
async def test_get_embeddings_batch_interface() -> None:
    """Verify batch embedding generation handles empty and multiple inputs."""
    assert await get_embeddings_batch([]) == []

    texts = [
        "Puella cantat.",
        "Senatus haec intellegit, consul videt.",
        "Horum omnium fortissimi sunt Belgae.",
    ]
    vecs = await get_embeddings_batch(texts)
    assert len(vecs) == 3
    assert all(len(v) == EMBEDDING_DIM for v in vecs)


def test_format_chunks_for_context_formatting() -> None:
    """Verify context formatting turns chunk dictionaries into readable prompt context."""
    empty_res = format_chunks_for_context([])
    assert "Nenhum fragmento" in empty_res

    chunks = [
        {
            "author": "Gaius Iulius Caesar",
            "title": "Commentarii de Bello Gallico",
            "citation": "Caes. Gal. 1.1",
            "content": "Gallia est omnis divisa in partes tres",
            "translation": "Toda a Gália está dividida em três partes",
        }
    ]
    formatted = format_chunks_for_context(chunks)
    assert "[1] Gaius Iulius Caesar" in formatted
    assert "Caes. Gal. 1.1" in formatted
    assert 'Latim: "Gallia est omnis divisa in partes tres"' in formatted
    assert 'Tradução / Notas: "Toda a Gália está dividida em três partes"' in formatted


@pytest.mark.asyncio
async def test_ingest_corpus_seed_idempotent(db_session: AsyncSession) -> None:
    """Verify ingest_corpus_seed ingests the library and does not duplicate on repeat runs."""
    # Ensure seed is present
    await ingest_corpus_seed(db_session)

    # Count docs
    docs_result = await db_session.execute(select(LibraryDocument))
    docs = docs_result.scalars().all()
    assert len(docs) >= 3

    # Count chunks
    chunks_result = await db_session.execute(select(DocumentChunk))
    chunks = chunks_result.scalars().all()
    assert len(chunks) >= 8

    # Second run should skip already existing titles
    added_count = await ingest_corpus_seed(db_session)
    assert added_count == 0


@pytest.mark.asyncio
async def test_search_library_chunks_pgvector(db_session: AsyncSession) -> None:
    """Verify semantic search over pgvector returns relevant chunks."""
    # Ensure corpus exists
    await ingest_corpus_seed(db_session)

    # 1. Broad search
    results = await search_library_chunks(
        db=db_session,
        query="Belgae Gallia fortissimi",
        top_k=2,
    )
    assert len(results) > 0
    first_hit = results[0]
    assert "chunk_id" in first_hit
    assert "content" in first_hit
    assert "author" in first_hit

    # 2. Author filter for Cicero
    cicero_results = await search_library_chunks(
        db=db_session,
        query="Catilina patientia senatus",
        top_k=2,
        author_filter="Cicero",
    )
    assert len(cicero_results) > 0
    for r in cicero_results:
        assert "Cicero" in r["author"]

    # 3. Era/category filter for Grammar
    grammar_results = await search_library_chunks(
        db=db_session,
        query="Caso Nominativo sujeito",
        top_k=2,
        era_filter="Grammar",
    )
    assert len(grammar_results) > 0
    for r in grammar_results:
        assert r["era_category"] == "Grammar"


@pytest.mark.asyncio
async def test_search_latin_library_langchain_tool(db_session: AsyncSession) -> None:
    """Verify the @tool search_latin_library LangChain tool execution."""
    await ingest_corpus_seed(db_session)

    result_text = await search_latin_library.ainvoke(
        {"query": "Gallia divisa", "author": "Caesar"}
    )
    assert isinstance(result_text, str)
    assert "Caesar" in result_text or "Gallia" in result_text

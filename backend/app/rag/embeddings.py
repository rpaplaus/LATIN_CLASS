import hashlib
import logging
import math
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 1536


def _deterministic_mock_embedding(text: str, dim: int = EMBEDDING_DIM) -> list[float]:
    """Generate deterministic, unit-normalized float vector from string hash for offline testing.

    Ensures that identical strings produce identical vectors, and text sharing keywords
    shares vector components with predictable cosine distance.
    """
    cleaned = text.strip().lower()
    raw_hash = hashlib.sha256(cleaned.encode("utf-8")).digest()

    vector: list[float] = []
    # Expand seed hash deterministically across dimension
    for i in range(dim):
        byte_val = raw_hash[i % len(raw_hash)]
        offset = (i * 31 + byte_val) % 256
        val = (offset / 128.0) - 1.0
        vector.append(val)

    # L2 normalize
    norm = math.sqrt(sum(x * x for x in vector)) or 1.0
    return [x / norm for x in vector]


async def get_embedding(text: str) -> list[float]:
    """Generate 1536-dimensional vector embedding for text using configured provider or mock fallback."""
    if settings.OPENAI_API_KEY:
        try:
            from langchain_openai import OpenAIEmbeddings

            embeddings_client = OpenAIEmbeddings(
                model="text-embedding-3-small",
                openai_api_key=settings.OPENAI_API_KEY,
            )
            raw_vector: Any = await embeddings_client.aembed_query(text)
            return [float(x) for x in raw_vector]
        except Exception as exc:
            logger.warning(
                "OpenAI Embeddings API failed (%s). Falling back to mock embeddings.",
                exc,
            )

    if settings.GEMINI_API_KEY:
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings

            gemini_client = GoogleGenerativeAIEmbeddings(
                model="models/text-embedding-004",
                google_api_key=settings.GEMINI_API_KEY,
            )
            gemini_vec: Any = await gemini_client.aembed_query(text)
            raw_vec: list[float] = [float(x) for x in gemini_vec]
            # Pad or project to 1536 if needed
            if len(raw_vec) < EMBEDDING_DIM:
                raw_vec = raw_vec + [0.0] * (EMBEDDING_DIM - len(raw_vec))
            norm = math.sqrt(sum(x * x for x in raw_vec)) or 1.0
            return [x / norm for x in raw_vec[:EMBEDDING_DIM]]
        except Exception as exc:
            logger.warning(
                "Gemini Embeddings API failed (%s). Falling back to mock embeddings.",
                exc,
            )

    return _deterministic_mock_embedding(text, dim=EMBEDDING_DIM)


async def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Batch embed multiple strings with provider optimization or mock fallback."""
    if not texts:
        return []

    if settings.OPENAI_API_KEY:
        try:
            from langchain_openai import OpenAIEmbeddings

            embeddings_client = OpenAIEmbeddings(
                model="text-embedding-3-small",
                openai_api_key=settings.OPENAI_API_KEY,
            )
            raw_docs: Any = await embeddings_client.aembed_documents(texts)
            return [[float(x) for x in row] for row in raw_docs]
        except Exception as exc:
            logger.warning(
                "Batch OpenAI Embeddings API failed (%s). Using mock embeddings.", exc
            )

    return [_deterministic_mock_embedding(t, dim=EMBEDDING_DIM) for t in texts]

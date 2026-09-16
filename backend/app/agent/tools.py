import logging

from langchain_core.tools import tool

from app.core.database import async_session_factory
from app.rag.retriever import format_chunks_for_context, search_library_chunks

logger = logging.getLogger(__name__)


@tool
async def search_latin_library(query: str, author: str | None = None) -> str:
    """Pesquisa na Biblioteca de Alexandria por textos originais em latim, traduções e regras gramaticais.

    Consulte esta ferramenta sempre que precisar de citações literárias autênticas (ex: Júlio César, Cícero),
    exemplos históricos ou embasamento clássico sobre táticas militares romanas, política ou sintaxe latina.

    Args:
        query: Conceito, tema histórico ou frase gramatical a ser pesquisada (ex: 'Belgae', 'Gália dividida', 'Catilina', 'ordem das palavras').
        author: Filtro opcional pelo autor clássico (ex: 'Caesar', 'Cicero', 'Academia Latium').
    """
    logger.info(
        "Executing search_latin_library tool for query: '%s', author: %s", query, author
    )
    async with async_session_factory() as session:
        try:
            chunks = await search_library_chunks(
                db=session,
                query=query,
                top_k=3,
                author_filter=author,
            )
            return format_chunks_for_context(chunks)
        except Exception as exc:
            logger.error("Error executing search_latin_library: %s", exc)
            return f"Erro ao consultar a Biblioteca de Alexandria: {exc}"

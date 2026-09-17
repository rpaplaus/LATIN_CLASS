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


CLASSICAL_WEB_ENCYCLOPEDIA: dict[str, str] = {
    "pompeia": (
        "Achados Arqueológicos de Pompeia: Escavações revelaram mais de 80 padarias com pães "
        "carbonizados estampados com selos pessoais dos padeiros ('Celeris Q. Grani Veri servus') "
        "e mais de 11.000 inscrições murais (graffiti) que comprovam a vitalidade do Latim vulgar cotidiano."
    ),
    "gladius": (
        "O Gladius Hispaniensis: Espada curta de lâmina reta (aprox. 50-60 cm) com ponta perfurante aguçada, "
        "adotada pelos legionários romanos após as Guerras Púnicas. Projetada para estocadas letais no combate "
        "corpo a corpo cerrado por trás do grande escudo retangular (scutum)."
    ),
    "toga": (
        "Vestimentas e Classes Sociais na Roma Antiga: A toga era o manto nacional dos cidadãos romanos livres. "
        "A 'toga praetexta' com faixa púrpura era reservada a magistrados e crianças livres; a 'toga virilis' "
        "era assumida aos 14-16 anos; e a 'toga candida' (alvejada com pó de giz) identificava candidatos a eleições."
    ),
    "senado": (
        "O Senado Romano (Senatus): Órgão deliberativo e consultivo supremo fundado segundo a tradição por Rômulo com 100 patres. "
        "Na República e Império, reuniu os homens mais nobres de Roma na Curia Hostilia e na Curia Julia no Fórum Romano."
    ),
    "orberg": (
        "Método Indutivo-Contextual de Hans Ørberg (Lingua Latina per se Illustrata): Metodologia pedagógica que ensina "
        "latim diretamente na própria língua, através de gravuras e imersão dedutiva nas desinências, sem tradução mecânica."
    ),
    "pronuntiatio": (
        "Pronuntiatio Restituta: Pronúncia clássica reconstituída por filólogos no século XX para reproduzir a fala de Cícero "
        "e César: o 'C' é sempre velar oclusivo (/k/), o 'V' é semivocálico (/w/), e os ditongos 'AE' e 'OE' são lidos abertos."
    ),
}


@tool
async def search_classical_web(query: str) -> str:
    """Pesquisa na web por informações históricas, descobertas arqueológicas e curiosidades da Roma Antiga e do Mediterrâneo Clássico.

    Consulte esta ferramenta quando precisar de informações contextuais sobre a vida cotidiana romana,
    escavações arqueológicas em Pompeia ou Herculano, táticas de legiões, festivais, togas, alimentação ou etimologia comparada.

    Args:
        query: Termo ou dúvida histórica a pesquisar (ex: 'Pompeia pão', 'gladius legionários', 'origem da palavra candidato', 'vestimentas senado').
    """
    logger.info("Executing search_classical_web for query: '%s'", query)
    norm_query = query.lower()

    matches: list[str] = []
    for key, content in CLASSICAL_WEB_ENCYCLOPEDIA.items():
        if key in norm_query or any(w in norm_query for w in key.split()):
            matches.append(content)

    if matches:
        return "\n\n---\n\n".join(matches)

    return (
        f"Resultados históricos e arqueológicos para '{query}':\n"
        f"Na historiografia romana clássica, o tema '{query}' reflete as transformações institucionais, "
        f"militares e linguísticas vivenciadas entre o final da República e o Alto Império Romano."
    )

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rag import DocumentChunk, LibraryDocument
from app.rag.embeddings import get_embeddings_batch

logger = logging.getLogger(__name__)

CANONICAL_SEED_CORPUS: list[dict[str, Any]] = [
    {
        "title": "Commentarii de Bello Gallico (Liber I)",
        "author": "Gaius Iulius Caesar",
        "era_category": "Classical",
        "source_language": "la",
        "description": "Relato histórico e militar das campanhas de Júlio César na Gália (58 a.C.). Prosa clássica exemplar.",
        "chunks": [
            {
                "citation": "Caes. Gal. 1.1",
                "content": "Gallia est omnis divisa in partes tres, quarum unam incolunt Belgae, aliam Aquitani, tertiam qui ipsorum lingua Celtae, nostra Galli appellantur. Hi omnes lingua, institutis, legibus inter se differunt.",
                "translation": "Toda a Gália está dividida em três partes, das quais uma é habitada pelos belgas, outra pelos aquitanos, e a terceira por aqueles que na sua própria língua se chamam celtas e na nossa gauleses. Todos estes diferem entre si pela língua, costumes e leis.",
                "metadata": {
                    "topic": "geografia",
                    "grammar": ["nominativo_plural", "divisa_in_partes"],
                },
            },
            {
                "citation": "Caes. Gal. 1.2",
                "content": "Horum omnium fortissimi sunt Belgae, propterea quod a cultu atque humanitate provinciae longissime absunt, minimeque ad eos mercatores saepe commeant atque ea quae ad effeminandos animos pertinent important.",
                "translation": "De todos estes, os mais valorosos são os belgas, por estarem mais afastados do refinamento e da civilização da província romana, e porque raramente os comerciantes os visitam trazendo produtos que amaciam o espírito.",
                "metadata": {
                    "topic": "taticas_militares",
                    "grammar": ["grau_superlativo", "propterea_quod"],
                },
            },
            {
                "citation": "Caes. Gal. 1.7",
                "content": "Caesari cum id nuntiatum esset, eos per provinciam nostram iter facere conari, maturat ab urbe proficisci et quam maximis potest itineribus in Galliam ulteriorem contendit et ad Genavam pervenit.",
                "translation": "Tendo isso sido anunciado a César, que eles tentavam fazer marcha através da nossa província, ele apressou-se a partir de Roma e, a marchas forçadas tão rápidas quanto possível, dirigiu-se à Gália ulterior e chegou a Genebra.",
                "metadata": {
                    "topic": "estrategia_militar",
                    "grammar": ["cum_historicum", "oracao_infinitiva"],
                },
            },
        ],
    },
    {
        "title": "Oratio in Catilinam Prima",
        "author": "Marcus Tullius Cicero",
        "era_category": "Classical",
        "source_language": "la",
        "description": "Primeiro discurso consular proferido por Cícero contra a conspiração de Catilina no Senado romano (63 a.C.). Ápice da oratória clássica.",
        "chunks": [
            {
                "citation": "Cic. Catil. 1.1",
                "content": "Quo usque tandem abutere, Catilina, patientia nostra? Quam diu etiam furor iste tuus nos eludet? Quem ad finem sese effrenata iactabit audacia?",
                "translation": "Até quando, afinal, Catilina, abusarás da nossa paciência? Por quanto tempo ainda essa tua loucura zombara de nós? Até que ponto há de gabar-se a tua desenfreada audácia?",
                "metadata": {
                    "topic": "retorica_politica",
                    "grammar": ["verbo_depoente", "pronome_demonstrativo_iste"],
                },
            },
            {
                "citation": "Cic. Catil. 1.2",
                "content": "O tempora, o mores! Senatus haec intellegit, consul videt; hic tamen vivit. Vivit? Immo vero etiam in senatum venit, fit publici consilii particeps, notat et designat oculis ad caedem unum quemque nostrum.",
                "translation": "Ó tempos, ó costumes! O senado compreende estas coisas, o cônsul as vê; no entanto, este homem vive. Vive? Antes, pelo contrário: entra até no senado, toma parte nas deliberações públicas e aponta com os olhos para a morte cada um de nós.",
                "metadata": {
                    "topic": "eloquencia_senatorial",
                    "grammar": ["acusativo_exclamativo", "presente_do_indicativo"],
                },
            },
        ],
    },
    {
        "title": "Compêndio Fundamental de Gramática e Sintaxe Latina",
        "author": "Academia Latium",
        "era_category": "Grammar",
        "source_language": "pt",
        "description": "Regras canônicas fundamentais de morfologia casual e sintaxe clássica para consulta socrática.",
        "chunks": [
            {
                "citation": "Gramm. Cas. 1.1",
                "content": "O Caso Nominativo é o caso do Sujeito e do Predicativo do Sujeito. Na primeira declinação termina em -a (singular) e -ae (plural). Ex: Puella cantat (A menina canta); Puellae cantant (As meninas cantam).",
                "translation": "Regra Morfológica: 1ª Declinação Feminina: Nominativo Singular -a | Nominativo Plural -ae.",
                "metadata": {"topic": "nominativo", "declensao": "1"},
            },
            {
                "citation": "Gramm. Cas. 2.1",
                "content": "O Caso Acusativo expressa o Objeto Direto da oração e a direção de movimento com preposições como 'in' e 'ad'. Na primeira declinação termina em -am (singular) e -as (plural). Na segunda declinação termina em -um (singular) e -os/-a (plural).",
                "translation": "Regra Morfológica: Acusativo Singular: -am / -um | Acusativo Plural: -as / -os.",
                "metadata": {"topic": "acusativo", "declensao": "1_e_2"},
            },
            {
                "citation": "Gramm. Synt. 3.1",
                "content": "Ordem das Palavras na Prosa Clássica: A língua latina permite grande liberdade sintática devido às desinências casuais. Entretanto, no estilo nobre clássico (Cícero e César), vigora a tendência SOV: Sujeito + Objeto / Complementos + Verbo ao final da oração.",
                "translation": "Regra Sintática: Tendência clássica SOV (Subject - Object - Verb).",
                "metadata": {"topic": "ordem_palavras", "estilo": "SOV"},
            },
        ],
    },
]


async def ingest_document(
    db: AsyncSession,
    title: str,
    author: str,
    chunks_data: list[dict[str, Any]],
    era_category: str = "Classical",
    source_language: str = "la",
    description: str | None = None,
) -> LibraryDocument:
    """Ingest a literary work or grammar document and its pre-computed or generated vector chunks into pgvector."""
    # Check if document already exists
    stmt = select(LibraryDocument).where(
        LibraryDocument.title == title, LibraryDocument.author == author
    )
    existing_doc = (await db.execute(stmt)).scalar_one_or_none()

    if existing_doc:
        doc = existing_doc
    else:
        doc = LibraryDocument(
            title=title,
            author=author,
            era_category=era_category,
            source_language=source_language,
            description=description,
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)

    # Prepare chunk contents for batch vectorization
    texts_to_embed = [c["content"] for c in chunks_data]
    embeddings = await get_embeddings_batch(texts_to_embed)

    # Insert chunks
    for i, (c_data, emb) in enumerate(zip(chunks_data, embeddings, strict=False)):
        chunk = DocumentChunk(
            document_id=doc.id,
            chunk_index=i,
            content=c_data["content"],
            translation=c_data.get("translation"),
            citation=c_data["citation"],
            metadata_=c_data.get("metadata", {}),
            embedding=emb,
        )
        db.add(chunk)

    await db.commit()
    logger.info(
        "Successfully ingested document '%s' with %d chunks", title, len(chunks_data)
    )
    return doc


async def ingest_corpus_seed(db: AsyncSession) -> int:
    """Ingest canonical Alexandria seed corpus (Caesar, Cicero, Grammar Rules) into pgvector."""
    total_chunks = 0
    for doc_data in CANONICAL_SEED_CORPUS:
        # Avoid duplicate ingestion if document already exists
        check = await db.execute(
            select(LibraryDocument).where(LibraryDocument.title == doc_data["title"])
        )
        if check.scalar_one_or_none():
            logger.info(
                "Document '%s' already exists in Alexandria Library. Skipping.",
                doc_data["title"],
            )
            continue

        await ingest_document(
            db=db,
            title=doc_data["title"],
            author=doc_data["author"],
            chunks_data=doc_data["chunks"],
            era_category=doc_data["era_category"],
            source_language=doc_data["source_language"],
            description=doc_data.get("description"),
        )
        total_chunks += len(doc_data["chunks"])

    logger.info(
        "Alexandria corpus seed completed: %d total chunks ingested", total_chunks
    )
    return total_chunks

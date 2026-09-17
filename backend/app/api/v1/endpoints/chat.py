import logging
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.llm_factory import ModelRole, get_llm_for_role
from app.agent.tools import search_classical_web, search_latin_library
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.chat import ChatInteractiveRequest, ChatInteractiveResponse

logger = logging.getLogger(__name__)

router = APIRouter()

MAGISTER_CHAT_SYSTEM_PROMPT = """Você é o Magister Latium, um sábio professor humanista de Latim e entusiasta da história da Roma Antiga.
Sua missão é responder às perguntas dos alunos com generosidade intelectual, elegância e clareza.
Diretrizes:
1. Conecte sempre a dúvida de vocabulário ou gramática à vida cotidiana, literatura ou história romana.
2. Seja encorajador e utilize termos latinos ocasionais de cordialidade ('Salve!', 'Optime!', 'Discipule carissime!').
3. Se foram fornecidos fragmentos da Biblioteca de Alexandria ou dados de pesquisa histórica, integre-os naturalmente à sua resposta.
4. Mantenha as respostas concisas, focadas e ricas em curiosidades culturais."""


@router.post("/interactive", response_model=ChatInteractiveResponse)
async def chat_with_magister(
    req: ChatInteractiveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Engage in interactive dialogue with Magister Latium, enriched with Alexandria RAG and Web Knowledge."""
    sources: list[str] = []
    historical_snippet: str | None = None
    query_lower = req.message.lower()

    # 1. Check if query benefits from Web Search (historical/archaeological questions)
    web_context = ""
    if any(
        kw in query_lower
        for kw in [
            "pompeia",
            "gladius",
            "toga",
            "senado",
            "orberg",
            "pronúncia",
            "pronuntiatio",
            "césar",
            "história",
            "comida",
            "pão",
            "candidato",
            "legião",
            "soldado",
        ]
    ):
        try:
            web_context = await search_classical_web.ainvoke({"query": req.message})
            if web_context and "Erro" not in web_context:
                sources.append("Pesquisa Histórica e Arqueológica (Web)")
                historical_snippet = (
                    web_context[:250] + "..." if len(web_context) > 250 else web_context
                )
        except Exception as exc:
            logger.warning("Classical web search tool failed: %s", exc)

    # 2. Check if query benefits from Alexandria RAG (grammar or Latin terms)
    alexandria_context = ""
    try:
        alexandria_context = await search_latin_library.ainvoke({"query": req.message})
        if (
            alexandria_context
            and "Erro" not in alexandria_context
            and "Nenhum fragmento" not in alexandria_context
        ):
            sources.append("Biblioteca de Alexandria (Textos Canônicos)")
    except Exception as exc:
        logger.warning("Alexandria RAG search failed: %s", exc)

    # 3. Generate Magister reply via LLM or curated humanistic fallback
    llm = get_llm_for_role(ModelRole.TUTOR)

    if llm is not None:
        try:
            prompt_content = (
                f"Dúvida do aluno {current_user.full_name}: {req.message}\n"
            )
            if req.context_topics:
                prompt_content += (
                    f"Tópicos da lição em andamento: {', '.join(req.context_topics)}\n"
                )
            if web_context:
                prompt_content += (
                    f"\nContexto Arqueológico / Histórico:\n{web_context}\n"
                )
            if alexandria_context:
                prompt_content += (
                    f"\nFragmentos Canônicos de Alexandria:\n{alexandria_context}\n"
                )

            messages = [
                {"role": "system", "content": MAGISTER_CHAT_SYSTEM_PROMPT},
                {"role": "user", "content": prompt_content},
            ]
            response = await llm.ainvoke(messages)
            reply_text = str(response.content).strip()
            return ChatInteractiveResponse(
                reply=reply_text,
                sources_consulted=sources,
                historical_trivia_snippet=historical_snippet,
            )
        except Exception as exc:
            logger.warning(
                "LLM chat invocation failed (%s). Falling back to mock Magister.", exc
            )

    # Deterministic fallback reply
    default_reply = f"Salve, {current_user.full_name}! Uma excelente indagação sobre a língua e os costumes romanos. "
    if (
        "pronúncia" in query_lower
        or "som" in query_lower
        or "césar" in query_lower
        or "veni" in query_lower
    ):
        default_reply += (
            "Na 'Pronuntiatio Restituta' (a pronúncia clássica reconstituída de Cícero e César), a letra 'C' soava invariavelmente "
            "como oclusiva velar (/k/), de modo que 'Caesar' soava 'Káesar'. Já o 'V' latino representava a semivogal /w/, "
            "fazendo 'Veni, vidi, vici' soar como 'Weni, widi, wiki'. Essa sonoridade marcial e ritmada conferia aos discursos do Fórum uma cadência inconfundível!"
        )
    elif "pompeia" in query_lower or "pão" in query_lower:
        default_reply += (
            "Pompeia é uma cápsula do tempo extraordinária! O pão romano redescoberto nas escavações demonstra "
            "como a língua latina estava presente no cotidiano mais simples: cada padeiro tinha seu carimbo oficial em bronze. "
            "No Latium AI, você aprende o latim dos grandes oradores sem perder de vista o latim das ruas!"
        )
    elif "toga" in query_lower or "candidato" in query_lower:
        default_reply += (
            "As vestimentas em Roma falavam tanto quanto as palavras. A 'toga candida', alvejada com pó de giz, "
            "dava aos postulantes ao Senado uma presença luminosa no Fórum Romano. É desta tradição que herdamos a palavra moderna 'candidato'!"
        )
    else:
        default_reply += (
            "No Latim, cada desinência carrega um significado preciso de função sintática. "
            "Ao dominar os casos (Nominativo para o sujeito, Acusativo para o objeto direto), você destrava "
            "a liberdade poética de construir frases elegantes onde a ordem das palavras serve à expressividade, não à rigidez!"
        )

    return ChatInteractiveResponse(
        reply=default_reply,
        sources_consulted=sources or ["Tradição Humanista Clássica"],
        historical_trivia_snippet=historical_snippet,
    )

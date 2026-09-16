import logging
from enum import StrEnum
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


class ModelRole(StrEnum):
    """Functional roles for LLMs across the Latium AI architecture."""

    ROUTER = "router"
    TUTOR = "tutor"
    EVALUATOR = "evaluator"
    ILLUSTRATOR = "illustrator"


def get_llm_for_role(role: ModelRole) -> Any | None:
    """Retrieve an initialized LLM client tailored to the specific functional role.

    Provides transparent fallback cascading:
    - ROUTER: Groq (Llama 3.1) -> OpenAI (gpt-4o-mini) -> Gemini (1.5-flash) -> None (local rule-based)
    - TUTOR: Anthropic (Claude 3.5 Sonnet) -> Gemini (1.5-pro) -> OpenAI (gpt-4o-mini) -> None (mock)
    - EVALUATOR: OpenAI (GPT-4o) -> Anthropic (Claude 3.5 Sonnet) -> Gemini (1.5-pro) -> None (mock)
    - ILLUSTRATOR: OpenAI (gpt-4o-mini) -> Anthropic (Claude 3.5 Sonnet) -> Gemini (1.5-flash) -> None (mock)
    """
    if role == ModelRole.ROUTER:
        if settings.GROQ_API_KEY:
            try:
                from langchain_groq import ChatGroq

                logger.info("Initializing Groq router LLM (%s)", settings.ROUTER_MODEL)
                return ChatGroq(
                    model_name=settings.ROUTER_MODEL,
                    api_key=settings.GROQ_API_KEY,
                    temperature=0.0,
                )
            except Exception as exc:
                logger.warning("Failed to initialize Groq router: %s", exc)

        if settings.OPENAI_API_KEY:
            try:
                from langchain_openai import ChatOpenAI

                logger.info("Falling back to OpenAI router LLM (gpt-4o-mini)")
                return ChatOpenAI(
                    model="gpt-4o-mini",
                    api_key=settings.OPENAI_API_KEY,
                    temperature=0.0,
                )
            except Exception as exc:
                logger.warning(
                    "Failed to initialize OpenAI fallback for router: %s", exc
                )

        if settings.GEMINI_API_KEY:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI

                logger.info("Falling back to Gemini router LLM (gemini-1.5-flash)")
                return ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash",
                    google_api_key=settings.GEMINI_API_KEY,
                    temperature=0.0,
                )
            except Exception as exc:
                logger.warning(
                    "Failed to initialize Gemini fallback for router: %s", exc
                )

        return None

    if role == ModelRole.TUTOR:
        if settings.ANTHROPIC_API_KEY:
            try:
                from langchain_anthropic import ChatAnthropic

                logger.info(
                    "Initializing Anthropic Tutor LLM (%s)", settings.TUTOR_MODEL
                )
                return ChatAnthropic(
                    model=settings.TUTOR_MODEL,
                    api_key=settings.ANTHROPIC_API_KEY,
                    temperature=0.3,
                )
            except Exception as exc:
                logger.warning("Failed to initialize Anthropic Tutor: %s", exc)

        if settings.GEMINI_API_KEY:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI

                logger.info("Falling back to Gemini Tutor LLM (gemini-1.5-pro)")
                return ChatGoogleGenerativeAI(
                    model="gemini-1.5-pro",
                    google_api_key=settings.GEMINI_API_KEY,
                    temperature=0.3,
                )
            except Exception as exc:
                logger.warning(
                    "Failed to initialize Gemini fallback for tutor: %s", exc
                )

        if settings.OPENAI_API_KEY:
            try:
                from langchain_openai import ChatOpenAI

                logger.info("Falling back to OpenAI Tutor LLM (gpt-4o-mini)")
                return ChatOpenAI(
                    model="gpt-4o-mini",
                    api_key=settings.OPENAI_API_KEY,
                    temperature=0.3,
                )
            except Exception as exc:
                logger.warning(
                    "Failed to initialize OpenAI fallback for tutor: %s", exc
                )

        return None

    if role == ModelRole.EVALUATOR:
        if settings.OPENAI_API_KEY:
            try:
                from langchain_openai import ChatOpenAI

                logger.info(
                    "Initializing OpenAI Evaluator LLM (%s)", settings.EVALUATOR_MODEL
                )
                return ChatOpenAI(
                    model=settings.EVALUATOR_MODEL,
                    api_key=settings.OPENAI_API_KEY,
                    temperature=0.1,
                )
            except Exception as exc:
                logger.warning("Failed to initialize OpenAI Evaluator: %s", exc)

        if settings.ANTHROPIC_API_KEY:
            try:
                from langchain_anthropic import ChatAnthropic

                logger.info(
                    "Falling back to Anthropic Evaluator LLM (claude-3-5-sonnet)"
                )
                return ChatAnthropic(
                    model="claude-3-5-sonnet-20241022",
                    api_key=settings.ANTHROPIC_API_KEY,
                    temperature=0.1,
                )
            except Exception as exc:
                logger.warning(
                    "Failed to initialize Anthropic fallback for evaluator: %s", exc
                )

        if settings.GEMINI_API_KEY:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI

                logger.info("Falling back to Gemini Evaluator LLM (gemini-1.5-pro)")
                return ChatGoogleGenerativeAI(
                    model="gemini-1.5-pro",
                    google_api_key=settings.GEMINI_API_KEY,
                    temperature=0.1,
                )
            except Exception as exc:
                logger.warning(
                    "Failed to initialize Gemini fallback for evaluator: %s", exc
                )

        return None

    if role == ModelRole.ILLUSTRATOR:
        if settings.OPENAI_API_KEY:
            try:
                from langchain_openai import ChatOpenAI

                logger.info("Initializing OpenAI Illustrator LLM (gpt-4o-mini)")
                return ChatOpenAI(
                    model="gpt-4o-mini",
                    api_key=settings.OPENAI_API_KEY,
                    temperature=0.7,
                )
            except Exception as exc:
                logger.warning("Failed to initialize OpenAI illustrator: %s", exc)

        if settings.GEMINI_API_KEY:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI

                logger.info("Falling back to Gemini Illustrator LLM (gemini-1.5-flash)")
                return ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash",
                    google_api_key=settings.GEMINI_API_KEY,
                    temperature=0.7,
                )
            except Exception as exc:
                logger.warning("Failed to initialize Gemini illustrator: %s", exc)

        return None

    return None

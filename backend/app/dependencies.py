"""Shared FastAPI dependencies."""

import logging
from functools import lru_cache
from langchain_groq import ChatGroq
from app.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_llm() -> ChatGroq | None:
    """Create and cache a ChatGroq instance.

    Returns None if no API key is configured, allowing fallback behavior.
    """
    if not settings.groq_api_key:
        logger.warning(
            "GROQ_API_KEY not set — LLM calls will use fallback responses"
        )
        return None

    try:
        llm = ChatGroq(
            model=settings.model_name,
            groq_api_key=settings.groq_api_key,
            temperature=settings.model_temperature,
            timeout=30,
            max_retries=2,
        )
        logger.info("LLM initialized: %s", settings.model_name)
        return llm
    except Exception as e:
        logger.error("Failed to initialize LLM: %s", e)
        return None

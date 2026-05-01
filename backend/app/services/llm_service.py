"""Core LLM invocation helper with structured output and retry logic."""

import logging
from typing import Type, TypeVar

from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel

from app.dependencies import get_llm

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def invoke_structured(
    system_prompt: str,
    user_prompt: str,
    schema: Type[T],
    retries: int = 2,
) -> T | None:
    """Invoke the LLM with structured output parsing.

    Args:
        system_prompt: The system message defining the agent's role.
        user_prompt: The user message with context.
        schema: Pydantic model class for structured output.
        retries: Number of retry attempts on failure.

    Returns:
        A parsed Pydantic model instance, or None if all attempts fail.
    """
    llm = get_llm()
    if llm is None:
        logger.warning("LLM unavailable — returning None for fallback handling")
        return None

    structured_llm = llm.with_structured_output(schema=schema)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    for attempt in range(1, retries + 1):
        try:
            result = structured_llm.invoke(messages)
            logger.info(
                "LLM call succeeded (attempt %d/%d) for %s",
                attempt,
                retries,
                schema.__name__,
            )
            return result
        except Exception as e:
            logger.error(
                "LLM call failed (attempt %d/%d) for %s: %s",
                attempt,
                retries,
                schema.__name__,
                e,
            )
            if attempt == retries:
                logger.error("All LLM retry attempts exhausted for %s", schema.__name__)
                return None

    return None

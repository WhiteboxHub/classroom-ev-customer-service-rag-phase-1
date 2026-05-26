"""OpenAI GPT integration for grounded generation."""

from typing import Optional

from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.core.exceptions import GenerationError
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMService:
    """OpenAI LLM wrapper with enterprise grounding defaults."""

    def __init__(self):
        if not settings.openai_api_key:
            logger.warning("openai_api_key_missing", msg="Set OPENAI_API_KEY for generation")
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            api_key=settings.openai_api_key or "not-set",
        )

    def get_llm(self) -> ChatOpenAI:
        if not settings.openai_api_key:
            raise GenerationError(
                "OpenAI API key not configured. Set OPENAI_API_KEY in .env"
            )
        return self.llm

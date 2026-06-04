"""LLM integration supporting Groq (free) and OpenAI providers."""

from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel

from app.core.config import settings
from app.core.exceptions import GenerationError
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMService:
    """Multi-provider LLM wrapper. Auto-detects Groq or OpenAI based on available API keys."""

    def __init__(self):
        self.llm: Optional[BaseChatModel] = None
        self._provider = settings.llm_provider

        if self._provider == "groq":
            self._init_groq()
        elif self._provider == "openai":
            self._init_openai()
        else:
            logger.warning(
                "no_llm_provider_configured",
                msg="Set GROQ_API_KEY (free) or OPENAI_API_KEY in .env",
            )

    def _init_groq(self) -> None:
        from langchain_groq import ChatGroq

        self.llm = ChatGroq(
            model=settings.groq_model,
            temperature=settings.openai_temperature,
            api_key=settings.groq_api_key,
        )
        logger.info(
            "llm_provider_initialized",
            provider="groq",
            model=settings.groq_model,
        )

    def _init_openai(self) -> None:
        from langchain_openai import ChatOpenAI

        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            api_key=settings.openai_api_key,
        )
        logger.info(
            "llm_provider_initialized",
            provider="openai",
            model=settings.openai_model,
        )

    def get_llm(self) -> BaseChatModel:
        if self.llm is None:
            raise GenerationError(
                "No LLM provider configured. "
                "Set GROQ_API_KEY (free at https://console.groq.com) "
                "or OPENAI_API_KEY in your .env file."
            )
        return self.llm

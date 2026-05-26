"""LangChain-style tracing callbacks for retrieval and LLM stages."""

from typing import Any, Dict, List, Optional
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler

from app.core.logging import get_logger

logger = get_logger(__name__)


class RAGTracingCallback(BaseCallbackHandler):
    """Trace retrieval and generation pipeline stages."""

    def __init__(self):
        self.events: List[Dict[str, Any]] = []

    def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        self.events.append({"event": "chain_start", "run_id": str(run_id)})

    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        logger.info("llm_start", run_id=str(run_id), prompt_chars=sum(len(p) for p in prompts))

    def on_retriever_start(
        self,
        serialized: Dict[str, Any],
        query: str,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        logger.info("retriever_start", query=query[:120], run_id=str(run_id))

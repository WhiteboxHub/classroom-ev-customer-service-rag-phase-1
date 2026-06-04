"""LangChain RetrievalQA-style grounded generation orchestration."""

from typing import Any, Dict, List, Optional, Tuple

from langchain_core.output_parsers import StrOutputParser

from app.core.logging import get_logger
from app.generation.llm_service import LLMService
from app.generation.prompts import CHAT_PROMPT
from app.memory.conversation_memory import ConversationMemoryManager

logger = get_logger(__name__)


class EVRAGChain:
    """Builds context from retrieved chunks and generates grounded responses."""

    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        memory_manager: Optional[ConversationMemoryManager] = None,
    ):
        self.llm_service = llm_service or LLMService()
        self.memory_manager = memory_manager or ConversationMemoryManager()

    def format_context(self, sources: List[Dict[str, Any]]) -> str:
        blocks = []
        for idx, src in enumerate(sources, start=1):
            meta = src.get("metadata", {})
            header = (
                f"[Source {idx}] file={src.get('source_file')} | "
                f"category={meta.get('diagnostic_category', 'n/a')} | "
                f"vehicle={meta.get('vehicle_model', 'n/a')}"
            )
            blocks.append(f"{header}\n{src.get('text', '')}")
        return "\n\n---\n\n".join(blocks)

    def build_citations(self, sources: List[Dict[str, Any]]) -> List[str]:
        citations = []
        for idx, src in enumerate(sources, start=1):
            citations.append(
                f"[{idx}] {src.get('source_file', 'unknown')} "
                f"(doc={src.get('document_id', 'n/a')}, chunk={src.get('chunk_id', 'n/a')})"
            )
        return citations

    def generate(
        self,
        question: str,
        sources: List[Dict[str, Any]],
        session_id: Optional[str] = None,
    ) -> Tuple[str, List[str], bool]:
        if not sources:
            return (
                "I could not find relevant EV troubleshooting documentation for your query. "
                "Please refine the question or upload additional service manuals.",
                [],
                False,
            )

        context = self.format_context(sources)
        citations = self.build_citations(sources)
        history_text = ""
        if session_id:
            history_text = self.memory_manager.get_history_text(session_id)

        llm = self.llm_service.get_llm()
        chain = CHAT_PROMPT | llm | StrOutputParser()

        answer = chain.invoke(
            {
                "context": context,
                "history": history_text or "No prior conversation.",
                "question": question,
            }
        )

        grounded = "cannot find supported guidance" not in answer.lower()
        if session_id:
            self.memory_manager.add_exchange(session_id, question, answer)

        return answer, citations, grounded

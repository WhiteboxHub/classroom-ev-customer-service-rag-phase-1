"""Multi-turn conversation memory for EV troubleshooting sessions."""

from typing import Dict, List, Optional

from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage

from app.core.logging import get_logger
from app.utils.helpers import generate_id

logger = get_logger(__name__)


class ConversationMemoryManager:
    """Session-aware conversation memory (LangChain pattern)."""

    def __init__(self):
        self._sessions: Dict[str, InMemoryChatMessageHistory] = {}

    def get_or_create_session(self, session_id: Optional[str] = None) -> str:
        sid = session_id or generate_id("session")
        if sid not in self._sessions:
            self._sessions[sid] = InMemoryChatMessageHistory()
        return sid

    def get_history(self, session_id: str) -> InMemoryChatMessageHistory:
        if session_id not in self._sessions:
            self._sessions[session_id] = InMemoryChatMessageHistory()
        return self._sessions[session_id]

    def get_history_text(self, session_id: str, max_turns: int = 6) -> str:
        history = self.get_history(session_id)
        messages = history.messages[-max_turns * 2 :]
        lines = []
        for msg in messages:
            role = "User" if isinstance(msg, HumanMessage) else "Assistant"
            lines.append(f"{role}: {msg.content}")
        return "\n".join(lines)

    def add_exchange(self, session_id: str, question: str, answer: str) -> None:
        history = self.get_history(session_id)
        history.add_user_message(question)
        history.add_ai_message(answer)

    def get_messages(self, session_id: str) -> List[dict]:
        history = self.get_history(session_id)
        result = []
        for msg in history.messages:
            role = "user" if isinstance(msg, HumanMessage) else "assistant"
            result.append({"role": role, "content": msg.content})
        return result

    def clear_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

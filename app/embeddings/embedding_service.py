"""Sentence Transformer MiniLM embedding service with LangChain wrapper."""

from functools import lru_cache
from typing import List

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.embeddings import Embeddings

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Instruction prefix improves retrieval intent (study guide 5.12.2)
RETRIEVAL_QUERY_PREFIX = (
    "Represent this EV troubleshooting query for retrieval: "
)


@lru_cache(maxsize=1)
def _get_langchain_embeddings() -> Embeddings:
    return HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


class EmbeddingService:
    """Generates document and query embeddings using MiniLM."""

    def __init__(self):
        self._embeddings = _get_langchain_embeddings()
        logger.info("embedding_service_initialized", model=settings.embedding_model)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._embeddings.embed_documents(texts)

    def embed_query(self, query: str, instruction_aware: bool = True) -> List[float]:
        formatted = f"{RETRIEVAL_QUERY_PREFIX}{query}" if instruction_aware else query
        return self._embeddings.embed_query(formatted)

    @property
    def langchain_embeddings(self) -> Embeddings:
        return self._embeddings

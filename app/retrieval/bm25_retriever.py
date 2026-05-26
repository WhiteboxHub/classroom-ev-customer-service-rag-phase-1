"""BM25 keyword retrieval for DTC codes, firmware IDs, and exact technical terms."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_core.documents import Document
from rank_bm25 import BM25Okapi

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class BM25Index:
    """Persistent BM25 index synchronized with Milvus ingestion."""

    def __init__(self, index_path: Optional[Path] = None):
        self.index_path = index_path or settings.bm25_index_path
        self._corpus: List[Dict[str, Any]] = []
        self._bm25: Optional[BM25Okapi] = None
        self._load()

    def _tokenize(self, text: str) -> List[str]:
        return text.lower().split()

    def _load(self) -> None:
        if self.index_path.exists():
            try:
                self._corpus = json.loads(self.index_path.read_text(encoding="utf-8"))
                if self._corpus:
                    self._rebuild()
            except Exception as exc:
                logger.warning("bm25_load_failed", error=str(exc))
                self._corpus = []

    def _save(self) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.index_path.write_text(json.dumps(self._corpus, ensure_ascii=False, indent=2), encoding="utf-8")

    def _rebuild(self) -> None:
        tokenized = [self._tokenize(item["text"]) for item in self._corpus]
        self._bm25 = BM25Okapi(tokenized) if tokenized else None

    def add_chunks(self, chunks: List[Document]) -> None:
        for chunk in chunks:
            self._corpus.append(
                {
                    "chunk_id": chunk.metadata.get("chunk_id", ""),
                    "text": chunk.page_content,
                    "document_id": chunk.metadata.get("document_id", ""),
                    "source_file": chunk.metadata.get("source_file", ""),
                    "metadata": {
                        k: v
                        for k, v in chunk.metadata.items()
                        if k not in {"chunk_id", "document_id", "source_file"}
                    },
                }
            )
        self._rebuild()
        self._save()
        logger.info("bm25_index_updated", total=len(self._corpus))

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        if not self._bm25 or not self._corpus:
            return []

        scores = self._bm25.get_scores(self._tokenize(query))
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]

        results: List[Dict[str, Any]] = []
        for idx, score in ranked:
            if score <= 0:
                continue
            item = self._corpus[idx]
            results.append(
                {
                    "chunk_id": item["chunk_id"],
                    "text": item["text"],
                    "score": float(score),
                    "document_id": item["document_id"],
                    "source_file": item["source_file"],
                    "metadata": item.get("metadata", {}),
                }
            )
        return results

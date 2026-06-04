"""Semantic chunking with RecursiveCharacterTextSplitter (study guide pattern)."""

from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Section-aware separators preserve troubleshooting step sequences
EV_SEPARATORS = [
    "\n## ",
    "\n### ",
    "\nStep ",
    "\nProcedure:",
    "\n\n",
    "\n",
    " ",
]


class ChunkingPipeline:
    """Context-aware chunking for EV diagnostic workflows."""

    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size or settings.chunk_size,
            chunk_overlap=chunk_overlap or settings.chunk_overlap,
            separators=EV_SEPARATORS,
            length_function=len,
        )

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        chunks = self.splitter.split_documents(documents)
        for idx, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = idx
        logger.info("chunking_complete", chunks=len(chunks))
        return chunks

"""PDF parsing using PyPDF (LangChain-compatible extraction)."""

from pathlib import Path
from typing import List

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

from app.core.exceptions import IngestionError
from app.core.logging import get_logger

logger = get_logger(__name__)


class PDFParser:
    """Extract text from EV technical PDFs while preserving page structure."""

    def parse(self, file_path: Path) -> List[Document]:
        if not file_path.exists():
            raise IngestionError(f"PDF not found: {file_path}")

        try:
            loader = PyPDFLoader(str(file_path))
            documents = loader.load()
        except Exception as exc:
            raise IngestionError(f"Failed to parse PDF: {file_path}", {"error": str(exc)}) from exc

        for idx, doc in enumerate(documents):
            doc.metadata.setdefault("page", idx + 1)
            doc.metadata["source_file"] = file_path.name
            doc.metadata["file_type"] = "pdf"

        logger.info("pdf_parsed", file=str(file_path), pages=len(documents))
        return documents

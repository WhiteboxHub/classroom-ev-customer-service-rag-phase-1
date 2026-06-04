"""
pdf_loader.py
Enterprise PDF document loader for EV service manuals, DTC catalogs, and firmware docs.
Uses PyPDF with fallback metadata extraction.
"""

import logging
from pathlib import Path
from typing import List, Optional

from langchain_core.documents import Document

from app.core.logging import get_logger

logger = get_logger(__name__)


class PDFDocumentLoader:
    """
    Production PDF loader for EV technical documentation.
    Extracts text per page and preserves page-level metadata.
    """

    def __init__(self, extract_images: bool = False):
        self.extract_images = extract_images

    def load(self, file_path: Path) -> List[Document]:
        """Load a PDF and return one Document per page."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"PDF not found: {file_path}")

        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise ImportError("pypdf is required for PDF loading: pip install pypdf") from exc

        reader = PdfReader(str(file_path))
        documents: List[Document] = []

        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if not text.strip():
                logger.debug("pdf_empty_page", file=file_path.name, page=page_num)
                continue

            doc = Document(
                page_content=text,
                metadata={
                    "source_file": file_path.name,
                    "file_type": "pdf",
                    "page_number": page_num,
                    "total_pages": len(reader.pages),
                    "file_path": str(file_path),
                    "loader": "PDFDocumentLoader",
                },
            )
            documents.append(doc)

        logger.info("pdf_loaded", file=file_path.name, pages=len(documents))
        return documents

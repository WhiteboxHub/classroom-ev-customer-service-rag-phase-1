"""
html_loader.py
Enterprise HTML document loader for EV knowledge base articles, wiki pages,
charging station documentation portals, and manufacturer support pages.
Uses BeautifulSoup for clean text extraction with structure preservation.
"""

import re
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

from langchain_core.documents import Document

from app.core.logging import get_logger

logger = get_logger(__name__)


class HTMLDocumentLoader:
    """
    HTML loader for EV documentation web pages and knowledge base articles.
    Strips navigation, headers, footers and extracts meaningful content sections.
    """

    def __init__(self, extract_tables: bool = True):
        self.extract_tables = extract_tables

    def load_from_file(self, file_path: Path) -> List[Document]:
        """Load HTML from a local file."""
        file_path = Path(file_path)
        html_content = file_path.read_text(encoding="utf-8", errors="replace")
        return self._parse_html(html_content, source=file_path.name)

    def load_from_url(self, url: str, timeout: int = 30) -> List[Document]:
        """
        Load HTML from a URL using httpx.
        For JavaScript-heavy pages, use PlaywrightLoader instead.
        """
        try:
            import httpx
        except ImportError as exc:
            raise ImportError("httpx is required: pip install httpx") from exc

        try:
            response = httpx.get(url, timeout=timeout, follow_redirects=True)
            response.raise_for_status()
            html_content = response.text
            logger.info("html_fetched", url=url, status=response.status_code)
            return self._parse_html(html_content, source=url)
        except Exception as exc:
            logger.error("html_fetch_failed", url=url, error=str(exc))
            raise

    def _parse_html(self, html_content: str, source: str) -> List[Document]:
        """Parse HTML and extract clean text segments."""
        try:
            from bs4 import BeautifulSoup
        except ImportError as exc:
            raise ImportError("beautifulsoup4 is required: pip install beautifulsoup4") from exc

        soup = BeautifulSoup(html_content, "html.parser")

        # Remove navigation, scripts, styles, footers
        for tag in soup.find_all(["nav", "header", "footer", "script", "style", "aside"]):
            tag.decompose()

        title = soup.title.string.strip() if soup.title and soup.title.string else ""

        # Extract sections by heading hierarchy
        sections: List[Document] = []
        current_heading = title
        current_text_parts = []

        for element in soup.find_all(["h1", "h2", "h3", "h4", "p", "li", "td"]):
            if element.name in ["h1", "h2", "h3", "h4"]:
                if current_text_parts:
                    text = " ".join(current_text_parts).strip()
                    if text:
                        sections.append(
                            Document(
                                page_content=text,
                                metadata={
                                    "source_file": source,
                                    "file_type": "html",
                                    "section_title": current_heading,
                                    "document_title": title,
                                    "loader": "HTMLDocumentLoader",
                                },
                            )
                        )
                current_heading = element.get_text(strip=True)
                current_text_parts = []
            else:
                text = element.get_text(strip=True)
                if text:
                    current_text_parts.append(text)

        # Flush last section
        if current_text_parts:
            text = " ".join(current_text_parts).strip()
            if text:
                sections.append(
                    Document(
                        page_content=text,
                        metadata={
                            "source_file": source,
                            "file_type": "html",
                            "section_title": current_heading,
                            "document_title": title,
                            "loader": "HTMLDocumentLoader",
                        },
                    )
                )

        logger.info("html_parsed", source=source, sections=len(sections))
        return sections

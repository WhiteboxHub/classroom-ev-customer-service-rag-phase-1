"""
confluence_loader.py
Atlassian Confluence loader for EV internal knowledge base pages.
Loads space pages via Confluence REST API v2.
"""

import os
from typing import Dict, List, Optional

from langchain_core.documents import Document

from app.core.logging import get_logger

logger = get_logger(__name__)


class ConfluenceLoader:
    """
    Confluence REST API document loader for EV engineering knowledge base.
    Fetches pages from configured spaces (e.g., EV-TECH, EV-OPS, EV-FIRMWARE).
    """

    # Default EV Confluence spaces
    EV_SPACES = ["EV-TECH", "EV-OPS", "EV-FIRMWARE", "EV-SAFETY", "EV-CHARGING"]

    def __init__(
        self,
        base_url: Optional[str] = None,
        username: Optional[str] = None,
        api_token: Optional[str] = None,
    ):
        self.base_url = base_url or os.getenv("CONFLUENCE_BASE_URL", "")
        self.username = username or os.getenv("CONFLUENCE_USERNAME", "")
        self.api_token = api_token or os.getenv("CONFLUENCE_API_TOKEN", "")

    def _get_auth(self):
        """Return HTTP Basic auth tuple."""
        return (self.username, self.api_token)

    def load_space(self, space_key: str, limit: int = 100) -> List[Document]:
        """
        Load all pages from a Confluence space.
        Returns LangChain Documents with section metadata.
        """
        if not self.base_url:
            logger.warning("confluence_not_configured", space=space_key)
            return []

        try:
            import httpx
        except ImportError as exc:
            raise ImportError("httpx required: pip install httpx") from exc

        url = f"{self.base_url}/wiki/rest/api/content"
        params = {
            "spaceKey": space_key,
            "expand": "body.storage,metadata.labels",
            "limit": limit,
            "type": "page",
        }

        documents: List[Document] = []
        try:
            response = httpx.get(url, params=params, auth=self._get_auth(), timeout=30)
            response.raise_for_status()
            data = response.json()

            for page in data.get("results", []):
                body_html = page.get("body", {}).get("storage", {}).get("value", "")
                clean_text = self._strip_html(body_html)
                if not clean_text.strip():
                    continue

                documents.append(
                    Document(
                        page_content=clean_text,
                        metadata={
                            "source_file": f"confluence_{page.get('id', 'unknown')}.txt",
                            "confluence_page_id": page.get("id"),
                            "confluence_title": page.get("title", ""),
                            "confluence_space": space_key,
                            "confluence_url": f"{self.base_url}/wiki{page.get('_links', {}).get('webui', '')}",
                            "file_type": "confluence",
                            "loader": "ConfluenceLoader",
                        },
                    )
                )
        except Exception as exc:
            logger.error("confluence_load_failed", space=space_key, error=str(exc))

        logger.info("confluence_loaded", space=space_key, pages=len(documents))
        return documents

    def load_ev_spaces(self) -> List[Document]:
        """Load all EV-related Confluence spaces."""
        all_docs: List[Document] = []
        for space in self.EV_SPACES:
            all_docs.extend(self.load_space(space))
        return all_docs

    @staticmethod
    def _strip_html(html: str) -> str:
        """Strip Confluence storage format HTML tags."""
        import re
        clean = re.sub(r"<[^>]+>", " ", html)
        clean = re.sub(r"\s+", " ", clean)
        return clean.strip()

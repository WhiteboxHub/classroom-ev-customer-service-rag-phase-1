"""
wiki_loader.py
Internal MediaWiki / DokuWiki loader for EV technical knowledge base.
Fetches pages via MediaWiki API for internal EV engineering wikis.
"""

import os
from typing import Dict, List, Optional

from langchain_core.documents import Document

from app.core.logging import get_logger

logger = get_logger(__name__)


class WikiLoader:
    """
    MediaWiki API loader for internal EV engineering wiki.
    Loads pages from categories like: EV_Troubleshooting, Battery_Diagnostics,
    Charging_Infrastructure, Firmware_Updates, DTC_Catalog.
    """

    EV_WIKI_CATEGORIES = [
        "EV_Troubleshooting",
        "Battery_Diagnostics",
        "Charging_Infrastructure",
        "Firmware_Updates",
        "DTC_Catalog",
        "OTA_Procedures",
        "Technician_Workflows",
        "Safety_Procedures",
    ]

    def __init__(
        self,
        api_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.api_url = api_url or os.getenv("WIKI_API_URL", "")
        self.username = username or os.getenv("WIKI_USERNAME", "")
        self.password = password or os.getenv("WIKI_PASSWORD", "")

    def get_category_pages(self, category: str) -> List[str]:
        """Get page titles from a MediaWiki category."""
        if not self.api_url:
            logger.warning("wiki_not_configured")
            return []

        try:
            import httpx
        except ImportError as exc:
            raise ImportError("httpx required: pip install httpx") from exc

        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Category:{category}",
            "cmlimit": "500",
            "format": "json",
        }

        try:
            response = httpx.get(self.api_url, params=params, timeout=30)
            response.raise_for_status()
            members = response.json().get("query", {}).get("categorymembers", [])
            return [m["title"] for m in members]
        except Exception as exc:
            logger.error("wiki_category_failed", category=category, error=str(exc))
            return []

    def load_page(self, title: str) -> Optional[Document]:
        """Load a single wiki page by title."""
        if not self.api_url:
            return None

        try:
            import httpx
        except ImportError:
            return None

        params = {
            "action": "query",
            "prop": "revisions",
            "titles": title,
            "rvprop": "content",
            "rvslots": "main",
            "format": "json",
            "formatversion": "2",
        }

        try:
            response = httpx.get(self.api_url, params=params, timeout=30)
            response.raise_for_status()
            pages = response.json().get("query", {}).get("pages", [])
            if not pages:
                return None

            page = pages[0]
            content = (
                page.get("revisions", [{}])[0]
                .get("slots", {})
                .get("main", {})
                .get("content", "")
            )

            if not content.strip():
                return None

            return Document(
                page_content=content,
                metadata={
                    "source_file": f"wiki_{title.replace(' ', '_')}.txt",
                    "wiki_title": title,
                    "wiki_url": f"{self.api_url.replace('/api.php', '')}/wiki/{title.replace(' ', '_')}",
                    "file_type": "wiki",
                    "loader": "WikiLoader",
                },
            )
        except Exception as exc:
            logger.error("wiki_page_failed", title=title, error=str(exc))
            return None

    def load_ev_wiki(self) -> List[Document]:
        """Load all EV wiki pages across all EV categories."""
        all_docs: List[Document] = []
        for category in self.EV_WIKI_CATEGORIES:
            titles = self.get_category_pages(category)
            for title in titles:
                doc = self.load_page(title)
                if doc:
                    all_docs.append(doc)
        logger.info("wiki_ev_loaded", total=len(all_docs))
        return all_docs

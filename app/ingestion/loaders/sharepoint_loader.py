"""
sharepoint_loader.py
Microsoft SharePoint loader for EV service documentation.
Connects to SharePoint Online via Microsoft Graph API.
"""

import os
from typing import Dict, List, Optional

from langchain_core.documents import Document

from app.core.logging import get_logger

logger = get_logger(__name__)


class SharePointLoader:
    """
    SharePoint Online document loader via Microsoft Graph API.
    Supports: docx, xlsx, pdf files from EV engineering SharePoint sites.
    """

    def __init__(
        self,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        site_url: Optional[str] = None,
    ):
        self.tenant_id = tenant_id or os.getenv("SHAREPOINT_TENANT_ID", "")
        self.client_id = client_id or os.getenv("SHAREPOINT_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("SHAREPOINT_CLIENT_SECRET", "")
        self.site_url = site_url or os.getenv("SHAREPOINT_SITE_URL", "")
        self._access_token: Optional[str] = None

    def _get_token(self) -> str:
        """Obtain OAuth2 access token via client credentials flow."""
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            logger.warning("sharepoint_credentials_missing")
            return ""

        try:
            import httpx
        except ImportError as exc:
            raise ImportError("httpx required: pip install httpx") from exc

        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "https://graph.microsoft.com/.default",
        }

        response = httpx.post(token_url, data=payload, timeout=30)
        response.raise_for_status()
        self._access_token = response.json()["access_token"]
        return self._access_token

    def load_drive_items(self, drive_id: str, folder_path: str = "/") -> List[Document]:
        """
        Load documents from a SharePoint document library.
        Returns LangChain Documents with SharePoint metadata.
        """
        if not self.site_url:
            logger.warning("sharepoint_not_configured")
            return []

        try:
            token = self._get_token()
            if not token:
                return []

            import httpx

            headers = {"Authorization": f"Bearer {token}"}
            url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:{folder_path}:/children"
            response = httpx.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            documents: List[Document] = []
            for item in response.json().get("value", []):
                if item.get("file"):
                    # Fetch file content
                    download_url = item.get("@microsoft.graph.downloadUrl", "")
                    if download_url:
                        content_resp = httpx.get(download_url, timeout=60)
                        content = content_resp.text
                        documents.append(
                            Document(
                                page_content=content,
                                metadata={
                                    "source_file": item.get("name", "unknown"),
                                    "sharepoint_id": item.get("id"),
                                    "sharepoint_url": item.get("webUrl", ""),
                                    "file_type": item.get("name", "").split(".")[-1],
                                    "loader": "SharePointLoader",
                                    "size_bytes": item.get("size", 0),
                                },
                            )
                        )
            logger.info("sharepoint_loaded", drive=drive_id, items=len(documents))
            return documents

        except Exception as exc:
            logger.error("sharepoint_load_failed", error=str(exc))
            return []

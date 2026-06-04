"""
Document loaders for the EV RAG ingestion pipeline.
Supports: PDF, HTML, Markdown, S3, SharePoint, Confluence, Wiki.
"""

from app.ingestion.loaders.pdf_loader import PDFDocumentLoader
from app.ingestion.loaders.html_loader import HTMLDocumentLoader
from app.ingestion.loaders.s3_loader import S3DocumentLoader
from app.ingestion.loaders.confluence_loader import ConfluenceLoader
from app.ingestion.loaders.sharepoint_loader import SharePointLoader
from app.ingestion.loaders.wiki_loader import WikiLoader

__all__ = [
    "PDFDocumentLoader",
    "HTMLDocumentLoader",
    "S3DocumentLoader",
    "ConfluenceLoader",
    "SharePointLoader",
    "WikiLoader",
]

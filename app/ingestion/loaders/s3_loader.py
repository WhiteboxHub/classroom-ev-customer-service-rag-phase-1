"""
s3_loader.py
AWS S3 document loader for EV service manuals, firmware packages,
and DTC catalogs stored in enterprise S3 buckets.
Adapted from the reference RAG project S3 loader pattern.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional

from langchain_core.documents import Document

from app.core.logging import get_logger

logger = get_logger(__name__)

# Default EV document bucket prefix structure
EV_BUCKET_PREFIXES = {
    "service_manuals": "ev-docs/service-manuals/",
    "firmware_updates": "ev-docs/firmware-updates/",
    "dtc_codes": "ev-docs/dtc-catalogs/",
    "charging_docs": "ev-docs/charging-infrastructure/",
    "battery_manuals": "ev-docs/battery-manuals/",
    "ota_release_notes": "ev-docs/ota-release-notes/",
    "technician_notes": "ev-docs/technician-notes/",
}


class S3DocumentLoader:
    """
    Enterprise S3 loader for EV technical documentation.
    Supports text, PDF metadata extraction, and folder-prefix filtering.
    """

    def __init__(
        self,
        bucket_name: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: str = "us-east-1",
    ):
        self.bucket_name = bucket_name or os.getenv("S3_BUCKET_NAME", "ev-rag-docs")
        self.region_name = region_name
        self._aws_access_key = aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID")
        self._aws_secret_key = aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY")
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import boto3
            except ImportError as exc:
                raise ImportError("boto3 is required for S3 loading: pip install boto3") from exc
            self._client = boto3.client(
                "s3",
                aws_access_key_id=self._aws_access_key,
                aws_secret_access_key=self._aws_secret_key,
                region_name=self.region_name,
            )
        return self._client

    def list_objects(self, prefix: str = "") -> List[str]:
        """List all document keys under a given S3 prefix."""
        client = self._get_client()
        keys = []
        paginator = client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if not key.endswith("/"):  # skip folder markers
                    keys.append(key)
        return keys

    def load(self, file_key: str) -> str:
        """Load raw text content from S3 object."""
        client = self._get_client()
        logger.info("s3_load", bucket=self.bucket_name, key=file_key)
        try:
            response = client.get_object(Bucket=self.bucket_name, Key=file_key)
            return response["Body"].read().decode("utf-8", errors="replace")
        except Exception as exc:
            logger.error("s3_load_failed", key=file_key, error=str(exc))
            raise

    def load_prefix(self, prefix: str, doc_category: str = "ev_document") -> List[Document]:
        """Load all documents under an S3 prefix as LangChain Documents."""
        keys = self.list_objects(prefix)
        documents: List[Document] = []

        for key in keys:
            try:
                content = self.load(key)
                file_name = key.split("/")[-1]
                documents.append(
                    Document(
                        page_content=content,
                        metadata={
                            "source_file": file_name,
                            "s3_key": key,
                            "s3_bucket": self.bucket_name,
                            "file_type": Path(file_name).suffix.lstrip("."),
                            "doc_category": doc_category,
                            "loader": "S3DocumentLoader",
                        },
                    )
                )
            except Exception as exc:
                logger.warning("s3_skip_failed_object", key=key, error=str(exc))

        logger.info("s3_prefix_loaded", prefix=prefix, count=len(documents))
        return documents

    def load_ev_category(self, category: str) -> List[Document]:
        """Load all documents for a specific EV document category."""
        prefix = EV_BUCKET_PREFIXES.get(category)
        if not prefix:
            raise ValueError(
                f"Unknown EV category '{category}'. Valid: {list(EV_BUCKET_PREFIXES.keys())}"
            )
        return self.load_prefix(prefix, doc_category=category)

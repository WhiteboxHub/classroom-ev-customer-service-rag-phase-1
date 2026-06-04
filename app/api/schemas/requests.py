"""API request schemas."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MetadataFilter(BaseModel):
    vehicle_model: Optional[str] = None
    firmware_version: Optional[str] = None
    charging_type: Optional[str] = None
    diagnostic_category: Optional[str] = None
    document_source: Optional[str] = None


class IngestRequest(BaseModel):
    source_path: Optional[str] = Field(
        None, description="Path to file or directory relative to data dir"
    )
    vehicle_model: Optional[str] = None
    firmware_version: Optional[str] = None
    charging_type: Optional[str] = None
    diagnostic_category: Optional[str] = None
    document_source: Optional[str] = "enterprise_upload"


class RetrievalRequest(BaseModel):
    query: str = Field(..., min_length=2)
    top_k: Optional[int] = None
    use_hybrid: bool = True
    use_rerank: bool = True
    metadata_filter: Optional[MetadataFilter] = None


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=2)
    session_id: Optional[str] = None
    top_k: Optional[int] = None
    use_hybrid: bool = True
    use_rerank: bool = True
    metadata_filter: Optional[MetadataFilter] = None
    include_sources: bool = True

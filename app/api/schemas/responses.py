"""API response schemas."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SourceChunk(BaseModel):
    chunk_id: str
    text: str
    score: float
    source_file: str
    document_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str
    version: str
    milvus: str
    redis: str
    timestamp: str


class IngestResponse(BaseModel):
    success: bool
    document_id: str
    chunks_indexed: int
    message: str
    documents: List[str] = Field(default_factory=list)


class RetrievalResponse(BaseModel):
    query: str
    sources: List[SourceChunk]
    latency_ms: float
    retrieval_mode: str


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: List[SourceChunk]
    citations: List[str]
    latency_ms: float
    grounded: bool
    history: List[ChatMessage] = Field(default_factory=list)


class DocumentInfo(BaseModel):
    document_id: str
    source_file: str
    vehicle_model: Optional[str] = None
    firmware_version: Optional[str] = None
    diagnostic_category: Optional[str] = None
    chunk_count: int = 0

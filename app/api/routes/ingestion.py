"""Document ingestion API endpoints."""

import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile

from app.api.dependencies import get_cache, get_ingestion_pipeline
from app.api.schemas.requests import IngestRequest
from app.api.schemas.responses import IngestResponse
from app.core.config import settings
from app.core.exceptions import IngestionError, to_http_exception
from app.core.logging import get_logger
from app.observability.metrics import metrics_collector

logger = get_logger(__name__)
router = APIRouter(prefix="/ingest", tags=["Ingestion"])


@router.post("/upload", response_model=IngestResponse)
async def upload_document(
    file: UploadFile = File(...),
    vehicle_model: Optional[str] = Form(None),
    firmware_version: Optional[str] = Form(None),
    charging_type: Optional[str] = Form(None),
    diagnostic_category: Optional[str] = Form(None),
) -> IngestResponse:
    try:
        dest = settings.upload_dir / file.filename
        with dest.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        overrides = {
            k: v
            for k, v in {
                "vehicle_model": vehicle_model,
                "firmware_version": firmware_version,
                "charging_type": charging_type,
                "diagnostic_category": diagnostic_category,
            }.items()
            if v
        }

        pipeline = get_ingestion_pipeline()
        result = pipeline.ingest_file(dest, overrides)
        metrics_collector.record_ingestion(result["chunks_indexed"])
        get_cache().invalidate_namespace("retrieval")
        get_cache().invalidate_namespace("chat")

        return IngestResponse(
            success=True,
            document_id=result["document_id"],
            chunks_indexed=result["chunks_indexed"],
            message=f"Ingested {file.filename} successfully",
            documents=[result["source_file"]],
        )
    except IngestionError as exc:
        raise to_http_exception(exc) from exc


@router.post("/path", response_model=IngestResponse)
async def ingest_from_path(request: IngestRequest) -> IngestResponse:
    try:
        overrides = {
            k: v
            for k, v in {
                "vehicle_model": request.vehicle_model,
                "firmware_version": request.firmware_version,
                "charging_type": request.charging_type,
                "diagnostic_category": request.diagnostic_category,
                "document_source": request.document_source,
            }.items()
            if v
        }
        pipeline = get_ingestion_pipeline()
        results = pipeline.ingest_path(
            request.source_path or "sample_ev_docs",
            overrides,
        )
        total_chunks = sum(r["chunks_indexed"] for r in results)
        metrics_collector.record_ingestion(total_chunks)
        get_cache().invalidate_namespace("retrieval")
        get_cache().invalidate_namespace("chat")

        return IngestResponse(
            success=True,
            document_id=results[-1]["document_id"] if results else "",
            chunks_indexed=total_chunks,
            message=f"Ingested {len(results)} document(s)",
            documents=[r["source_file"] for r in results],
        )
    except IngestionError as exc:
        raise to_http_exception(exc) from exc


@router.get("/documents")
async def list_documents() -> dict:
    store = get_ingestion_pipeline().vector_store
    return {"documents": store.list_documents()}

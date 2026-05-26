"""FastAPI application entry point for EV RAG Phase-1."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.middleware.logging_middleware import RequestLoggingMiddleware
from app.api.routes import chat, health, ingestion, retrieval
from app.core.config import settings
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.ensure_dirs()
    logger.info("ev_rag_startup", version=__version__)
    yield
    logger.info("ev_rag_shutdown")


app = FastAPI(
    title="EV RAG Platform - Phase 1",
    description="Enterprise EV troubleshooting RAG with hybrid retrieval and grounded generation",
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

api_prefix = settings.api_prefix
app.include_router(health.router, prefix=api_prefix)
app.include_router(ingestion.router, prefix=api_prefix)
app.include_router(retrieval.router, prefix=api_prefix)
app.include_router(chat.router, prefix=api_prefix)


@app.get("/")
async def root():
    return {
        "service": "EV RAG Platform",
        "version": __version__,
        "docs": "/docs",
        "api_prefix": api_prefix,
    }

"""
Asynchronous worker package for the EV RAG platform.
Powered by Celery with Redis as the message broker.
Workers handle: document ingestion, embedding backfill, vector sync.
"""

from app.workers.celery_app import celery_app

__all__ = ["celery_app"]

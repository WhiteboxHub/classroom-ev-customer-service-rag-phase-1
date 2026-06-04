"""
celery_app.py
Celery application instance for the EV RAG Platform.
Broker: Redis   |   Backend: Redis
Worker queues: ingestion, embedding, sync, default
"""

import os

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "ev_rag_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.workers.tasks.ingestion_tasks",
        "app.workers.tasks.embedding_tasks",
        "app.workers.tasks.sync_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.workers.tasks.ingestion_tasks.*": {"queue": "ingestion"},
        "app.workers.tasks.embedding_tasks.*": {"queue": "embedding"},
        "app.workers.tasks.sync_tasks.*": {"queue": "sync"},
    },
    task_track_started=True,
    result_expires=86400,  # 24 hours
)


if __name__ == "__main__":
    celery_app.start()

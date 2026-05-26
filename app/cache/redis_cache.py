"""Redis caching for embeddings, retrieval, and API responses."""

import json
from typing import Any, Optional

import redis

from app.core.config import settings
from app.core.logging import get_logger
from app.utils.helpers import hash_text

logger = get_logger(__name__)


class RedisCache:
    """Enterprise cache layer with TTL and graceful degradation."""

    def __init__(self):
        self._client: Optional[redis.Redis] = None
        self._available = False
        if settings.cache_enabled:
            self._connect()

    def _connect(self) -> None:
        try:
            self._client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password or None,
                decode_responses=True,
                socket_connect_timeout=2,
            )
            self._client.ping()
            self._available = True
            logger.info("redis_connected", host=settings.redis_host)
        except Exception as exc:
            logger.warning("redis_unavailable", error=str(exc))
            self._available = False

    def health_check(self) -> str:
        if not self._available or not self._client:
            return "unavailable"
        try:
            self._client.ping()
            return "healthy"
        except Exception:
            return "unavailable"

    def _key(self, namespace: str, raw: str) -> str:
        return f"evrag:{namespace}:{hash_text(raw)}"

    def get(self, namespace: str, raw_key: str) -> Optional[Any]:
        if not self._available or not self._client:
            return None
        try:
            data = self._client.get(self._key(namespace, raw_key))
            return json.loads(data) if data else None
        except Exception:
            return None

    def set(self, namespace: str, raw_key: str, value: Any, ttl: Optional[int] = None) -> None:
        if not self._available or not self._client:
            return
        try:
            self._client.setex(
                self._key(namespace, raw_key),
                ttl or settings.cache_ttl_seconds,
                json.dumps(value),
            )
        except Exception as exc:
            logger.warning("redis_set_failed", error=str(exc))

    def invalidate_namespace(self, namespace: str) -> int:
        if not self._available or not self._client:
            return 0
        pattern = f"evrag:{namespace}:*"
        deleted = 0
        for key in self._client.scan_iter(match=pattern):
            self._client.delete(key)
            deleted += 1
        return deleted

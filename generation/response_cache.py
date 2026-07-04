import hashlib
import json

import redis

from backend.config import get_settings
from backend.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class ResponseCache:

    def __init__(self):
        self._redis: redis.Redis | None = None

    def _get_redis(self) -> redis.Redis | None:
        if self._redis is None:
            try:
                self._redis = redis.Redis(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    db=settings.redis_db,
                    decode_responses=True,
                )
                self._redis.ping()
            except Exception:
                logger.warning("Redis unavailable — response cache disabled")
                self._redis = None
        return self._redis

    def _make_key(self, query: str, document_ids: list[str] | None) -> str:
        doc_part = ",".join(sorted(document_ids)) if document_ids else "all"
        raw_key = f"{query.lower().strip()}::{doc_part}"
        return f"response:{hashlib.md5(raw_key.encode('utf-8')).hexdigest()}"

    def get(self, query: str, document_ids: list[str] | None = None) -> dict | None:
        r = self._get_redis()
        if r is None:
            return None
        try:
            key = self._make_key(query, document_ids)
            cached = r.get(key)
            if cached:
                logger.info("Response cache hit", query=query[:50])
                return json.loads(cached)
        except Exception:
            pass
        return None

    def set(self, query: str, document_ids: list[str] | None, response: dict) -> None:
        r = self._get_redis()
        if r is None:
            return
        try:
            key = self._make_key(query, document_ids)
            r.setex(key, settings.query_cache_ttl, json.dumps(response))
        except Exception:
            pass
import hashlib
import json
from typing import Any

import numpy as np
import redis
from sentence_transformers import SentenceTransformer

from backend.config import get_settings
from backend.core.exceptions import EmbeddingError
from backend.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class TextEmbedder:

    def __init__(self):
        self._model: SentenceTransformer | None = None
        self._redis: redis.Redis | None = None

    def _load_model(self) -> SentenceTransformer:
        if self._model is None:
            logger.info("Loading text embedding model", model=settings.text_embedding_model)
            self._model = SentenceTransformer(settings.text_embedding_model)
            logger.info("Text embedding model loaded")
        return self._model

    def _get_redis(self) -> redis.Redis | None:
        if self._redis is None:
            try:
                self._redis = redis.Redis(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    db=settings.redis_db,
                    decode_responses=False,
                )
                self._redis.ping()
            except Exception:
                logger.warning("Redis unavailable — embedding cache disabled")
                self._redis = None
        return self._redis

    def _make_cache_key(self, text: str) -> str:
        text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
        model_id = settings.text_embedding_model.replace("/", "_")
        return f"emb:text:{model_id}:{text_hash}"

    def _get_cached(self, key: str) -> list[float] | None:
        r = self._get_redis()
        if r is None:
            return None
        try:
            cached = r.get(key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass
        return None

    def _set_cached(self, key: str, embedding: list[float]) -> None:
        r = self._get_redis()
        if r is None:
            return
        try:
            r.setex(key, settings.embedding_cache_ttl, json.dumps(embedding))
        except Exception:
            pass

    def embed_text(self, text: str) -> list[float]:
        if not text or not text.strip():
            raise EmbeddingError(reason="Cannot embed empty text.")

        cache_key = self._make_cache_key(text)
        cached = self._get_cached(cache_key)
        if cached:
            logger.debug("Embedding cache hit", key=cache_key)
            return cached

        try:
            model = self._load_model()
            vector = model.encode(text, normalize_embeddings=True)
            embedding = vector.tolist()
            self._set_cached(cache_key, embedding)
            return embedding

        except Exception as e:
            raise EmbeddingError(reason=str(e))

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        results: list[list[float] | None] = [None] * len(texts)
        uncached_indices: list[int] = []
        uncached_texts: list[str] = []

        for i, text in enumerate(texts):
            if not text or not text.strip():
                results[i] = [0.0] * settings.text_embedding_dim
                continue
            cache_key = self._make_cache_key(text)
            cached = self._get_cached(cache_key)
            if cached:
                results[i] = cached
            else:
                uncached_indices.append(i)
                uncached_texts.append(text)

        if uncached_texts:
            try:
                model = self._load_model()
                logger.info("Embedding batch", count=len(uncached_texts))
                vectors = model.encode(
                    uncached_texts,
                    normalize_embeddings=True,
                    batch_size=32,
                    show_progress_bar=len(uncached_texts) > 50,
                )
                for idx, vector in zip(uncached_indices, vectors):
                    embedding = vector.tolist()
                    results[idx] = embedding
                    cache_key = self._make_cache_key(texts[idx])
                    self._set_cached(cache_key, embedding)

            except Exception as e:
                raise EmbeddingError(reason=str(e))

        return [r for r in results if r is not None]

    def embed_chunks(self, chunks: list[Any]) -> list[tuple[Any, list[float]]]:
        if not chunks:
            return []

        texts = [chunk.content for chunk in chunks]
        embeddings = self.embed_batch(texts)

        return list(zip(chunks, embeddings))
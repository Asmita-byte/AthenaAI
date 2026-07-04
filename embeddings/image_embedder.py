import hashlib
import json
from pathlib import Path

import numpy as np
import redis
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

from backend.config import get_settings
from backend.core.exceptions import EmbeddingError
from backend.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class ImageEmbedder:

    def __init__(self):
        self._model: CLIPModel | None = None
        self._processor: CLIPProcessor | None = None
        self._redis: redis.Redis | None = None

    def _load_model(self) -> tuple[CLIPModel, CLIPProcessor]:
        if self._model is None:
            logger.info("Loading CLIP model", model=settings.image_embedding_model)
            self._model = CLIPModel.from_pretrained(settings.image_embedding_model)
            self._processor = CLIPProcessor.from_pretrained(settings.image_embedding_model)
            logger.info("CLIP model loaded")
        return self._model, self._processor

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
                logger.warning("Redis unavailable — image embedding cache disabled")
                self._redis = None
        return self._redis

    def _make_cache_key(self, image_path: str) -> str:
        path_hash = hashlib.md5(image_path.encode("utf-8")).hexdigest()
        model_id = settings.image_embedding_model.replace("/", "_")
        return f"emb:image:{model_id}:{path_hash}"

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

    def embed_image(self, image_path: str) -> list[float]:
        cache_key = self._make_cache_key(image_path)
        cached = self._get_cached(cache_key)
        if cached:
            logger.debug("Image embedding cache hit", path=image_path)
            return cached

        try:
            import torch
            model, processor = self._load_model()
            image = Image.open(image_path).convert("RGB")
            inputs = processor(images=image, return_tensors="pt")

            with torch.no_grad():
                output = model.get_image_features(**inputs)
                features = output.pooler_output if hasattr(output, "pooler_output") else output
                features = features / features.norm(p=2, dim=-1, keepdim=True)

            embedding = features[0].tolist()
            self._set_cached(cache_key, embedding)
            return embedding

        except Exception as e:
            raise EmbeddingError(reason=f"Image embedding failed for {image_path}: {str(e)}")

    def embed_text_for_image_search(self, text: str) -> list[float]:
        try:
            import torch
            model, processor = self._load_model()
            inputs = processor(text=[text], return_tensors="pt", padding=True)

            with torch.no_grad():
                output = model.get_text_features(**inputs)
                features = output.pooler_output if hasattr(output, "pooler_output") else output
                features = features / features.norm(p=2, dim=-1, keepdim=True)

            return features[0].tolist()

        except Exception as e:
            raise EmbeddingError(reason=f"Text-for-image embedding failed: {str(e)}")
    

    def embed_image_chunks(self, chunks: list) -> list[tuple]:
        results = []
        for chunk in chunks:
            if chunk.image is None:
                continue
            try:
                embedding = self.embed_image(chunk.image.image_path)
                results.append((chunk, embedding))
            except EmbeddingError as e:
                logger.warning("Skipping image chunk", error=str(e))
        return results
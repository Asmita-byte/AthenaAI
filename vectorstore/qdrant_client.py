from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from backend.config import get_settings
from backend.core.exceptions import VectorStoreError
from backend.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

_client: QdrantClient | None = None


def get_qdrant_client() -> QdrantClient:
    global _client

    if _client is None:
        try:
            if settings.qdrant_use_memory:
                logger.info("Connecting to Qdrant (in-memory mode)")
                _client = QdrantClient(location=":memory:")
            else:
                logger.info(
                    "Connecting to Qdrant (server mode)",
                    host=settings.qdrant_host,
                    port=settings.qdrant_port,
                )
                _client = QdrantClient(
                    host=settings.qdrant_host,
                    port=settings.qdrant_port,
                    api_key=settings.qdrant_api_key,
                    https=settings.qdrant_https,
                )

            logger.info("Qdrant client connected")

        except Exception as e:
            raise VectorStoreError(operation="connect", reason=str(e))

    return _client


def ensure_collections() -> None:
    client = get_qdrant_client()

    _ensure_collection(
        client,
        collection_name=settings.qdrant_text_collection,
        vector_size=settings.text_embedding_dim,
    )

    _ensure_collection(
        client,
        collection_name=settings.qdrant_image_collection,
        vector_size=settings.image_embedding_dim,
    )


def _ensure_collection(client: QdrantClient, collection_name: str, vector_size: int) -> None:
    try:
        existing_collections = client.get_collections().collections
        existing_names = [c.name for c in existing_collections]

        if collection_name in existing_names:
            logger.info("Collection already exists", collection=collection_name)
            return

        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
        logger.info(
            "Collection created",
            collection=collection_name,
            vector_size=vector_size,
        )

    except Exception as e:
        raise VectorStoreError(
            operation=f"create_collection({collection_name})",
            reason=str(e),
        )


def get_collection_info(collection_name: str) -> dict:
    client = get_qdrant_client()
    try:
        info = client.get_collection(collection_name)
        return {
            "name": collection_name,
            "vectors_count": info.points_count,
            "status": info.status,
        }
    except Exception as e:
        raise VectorStoreError(operation="get_collection_info", reason=str(e))

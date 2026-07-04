import uuid

from qdrant_client.models import PointStruct

from backend.config import get_settings
from backend.core.exceptions import VectorStoreError
from backend.core.logging import get_logger
from vectorstore.collections import ImageChunkPayload, TextChunkPayload
from vectorstore.qdrant_client import get_qdrant_client

settings = get_settings()
logger = get_logger(__name__)


class VectorIndexer:

    def __init__(self):
        self.client = get_qdrant_client()

    def index_text_chunks(
        self,
        chunk_embedding_pairs: list[tuple],
        document_id: str,
    ) -> list[str]:
        if not chunk_embedding_pairs:
            return []

        points = []
        qdrant_ids = []

        for chunk, embedding in chunk_embedding_pairs:
            qdrant_id = str(uuid.uuid4())
            qdrant_ids.append(qdrant_id)

            payload = TextChunkPayload(
                chunk_id=qdrant_id,
                document_id=document_id,
                chunk_type=chunk.chunk_type,
                content=chunk.content,
                page_number=chunk.page_number,
                section_title=chunk.section_title or "",
                source_filename=chunk.source_filename or "",
            )

            points.append(
                PointStruct(
                    id=qdrant_id,
                    vector=embedding,
                    payload=payload.to_dict(),
                )
            )

        try:
            self.client.upsert(
                collection_name=settings.qdrant_text_collection,
                points=points,
            )
            logger.info(
                "Text chunks indexed",
                document_id=document_id,
                count=len(points),
            )
            return qdrant_ids

        except Exception as e:
            raise VectorStoreError(operation="index_text_chunks", reason=str(e))

    def index_image_chunks(
        self,
        chunk_embedding_pairs: list[tuple],
        document_id: str,
    ) -> list[str]:
        if not chunk_embedding_pairs:
            return []

        points = []
        qdrant_ids = []

        for chunk, embedding in chunk_embedding_pairs:
            qdrant_id = str(uuid.uuid4())
            qdrant_ids.append(qdrant_id)

            payload = ImageChunkPayload(
                chunk_id=qdrant_id,
                document_id=document_id,
                chunk_type=chunk.chunk_type,
                content=chunk.content,
                page_number=chunk.page_number,
                image_path=chunk.image.image_path if chunk.image else "",
                source_filename=chunk.source_filename or "",
            )

            points.append(
                PointStruct(
                    id=qdrant_id,
                    vector=embedding,
                    payload=payload.to_dict(),
                )
            )

        try:
            self.client.upsert(
                collection_name=settings.qdrant_image_collection,
                points=points,
            )
            logger.info(
                "Image chunks indexed",
                document_id=document_id,
                count=len(points),
            )
            return qdrant_ids

        except Exception as e:
            raise VectorStoreError(operation="index_image_chunks", reason=str(e))

    def delete_document_vectors(self, document_id: str) -> None:
        from qdrant_client.models import FieldCondition, Filter, MatchValue

        filter_condition = Filter(
            must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
        )

        try:
            self.client.delete(
                collection_name=settings.qdrant_text_collection,
                points_selector=filter_condition,
            )
            self.client.delete(
                collection_name=settings.qdrant_image_collection,
                points_selector=filter_condition,
            )
            logger.info("Document vectors deleted", document_id=document_id)

        except Exception as e:
            raise VectorStoreError(operation="delete_document_vectors", reason=str(e))

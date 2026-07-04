from backend.config import get_settings
from backend.core.exceptions import RetrievalError
from backend.core.logging import get_logger
from embeddings.text_embedder import TextEmbedder
from vectorstore.qdrant_client import get_qdrant_client

settings = get_settings()
logger = get_logger(__name__)


class DenseRetriever:

    def __init__(self, text_embedder: TextEmbedder | None = None):
        self.client = get_qdrant_client()
        self.text_embedder = text_embedder or TextEmbedder()

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        document_ids: list[str] | None = None,
        collection_name: str | None = None,
    ) -> list[dict]:
        top_k = top_k or settings.retrieval_top_k_dense
        collection_name = collection_name or settings.qdrant_text_collection

        try:
            query_vector = self.text_embedder.embed_text(query)

            query_filter = None
            if document_ids:
                from qdrant_client.models import FieldCondition, Filter, MatchAny
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchAny(any=document_ids),
                        )
                    ]
                )

            results = self.client.query_points(
                collection_name=collection_name,
                query=query_vector,
                limit=top_k,
                query_filter=query_filter,
                with_payload=True,
            )

            chunks = []
            for point in results.points:
                chunks.append(
                    {
                        "id": point.id,
                        "score": point.score,
                        "payload": point.payload,
                    }
                )

            logger.info(
                "Dense retrieval complete",
                query=query[:50],
                results_count=len(chunks),
            )

            return chunks

        except Exception as e:
            raise RetrievalError(reason=f"Dense retrieval failed: {str(e)}")
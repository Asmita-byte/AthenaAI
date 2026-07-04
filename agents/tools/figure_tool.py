from backend.config import get_settings
from backend.core.logging import get_logger
from embeddings.image_embedder import ImageEmbedder
from vectorstore.qdrant_client import get_qdrant_client

settings = get_settings()
logger = get_logger(__name__)


class FigureTool:

    name = "figure_retriever"
    description = (
        "Retrieves relevant figures, diagrams, and images from documents using cross-modal search."
    )

    def __init__(self, image_embedder: ImageEmbedder | None = None):
        self.image_embedder = image_embedder or ImageEmbedder()
        self.client = get_qdrant_client()

    def run(self, query: str, document_ids: list[str] | None = None, top_k: int = 5) -> list[dict]:
        logger.info("FigureTool invoked", query=query[:50])

        try:
            query_vector = self.image_embedder.embed_text_for_image_search(query)

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
                collection_name=settings.qdrant_image_collection,
                query=query_vector,
                limit=top_k,
                query_filter=query_filter,
                with_payload=True,
            )

            figure_results = [
                {"id": point.id, "score": point.score, "payload": point.payload}
                for point in results.points
            ]

            logger.info("FigureTool complete", results_count=len(figure_results))
            return figure_results

        except Exception as e:
            logger.warning("FigureTool failed", error=str(e))
            return []

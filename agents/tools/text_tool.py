from backend.core.logging import get_logger
from retrieval.hybrid_retriever import HybridRetriever

logger = get_logger(__name__)


class TextTool:

    name = "text_retriever"
    description = "Retrieves relevant text passages from documents based on semantic and keyword search."

    def __init__(self, retriever: HybridRetriever | None = None):
        self.retriever = retriever or HybridRetriever()

    def run(self, query: str, document_ids: list[str] | None = None) -> list[dict]:
        logger.info("TextTool invoked", query=query[:50])

        results = self.retriever.retrieve(
            query=query,
            document_ids=document_ids,
        )

        text_results = [
            r for r in results
            if r.get("payload", {}).get("chunk_type") == "text"
        ]

        logger.info("TextTool complete", results_count=len(text_results))
        return text_results
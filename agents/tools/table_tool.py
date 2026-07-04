from backend.core.logging import get_logger
from retrieval.hybrid_retriever import HybridRetriever

logger = get_logger(__name__)


class TableTool:

    name = "table_retriever"
    description = "Retrieves relevant tables and tabular data from documents based on the query."

    def __init__(self, retriever: HybridRetriever | None = None):
        self.retriever = retriever or HybridRetriever()

    def run(self, query: str, document_ids: list[str] | None = None) -> list[dict]:
        logger.info("TableTool invoked", query=query[:50])

        results = self.retriever.retrieve(
            query=query,
            document_ids=document_ids,
        )

        table_results = [r for r in results if r.get("payload", {}).get("chunk_type") == "table"]

        logger.info("TableTool complete", results_count=len(table_results))
        return table_results

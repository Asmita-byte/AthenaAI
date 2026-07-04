from backend.config import get_settings
from backend.core.logging import get_logger
from retrieval.dense_retriever import DenseRetriever
from retrieval.fusion import RRFFusion
from retrieval.reranker import Reranker
from retrieval.sparse_retriever import SparseRetriever

settings = get_settings()
logger = get_logger(__name__)


class HybridRetriever:

    def __init__(
        self,
        dense_retriever: DenseRetriever | None = None,
        sparse_retriever: SparseRetriever | None = None,
        fusion: RRFFusion | None = None,
        reranker: Reranker | None = None,
    ):
        self.dense_retriever = dense_retriever or DenseRetriever()
        self.sparse_retriever = sparse_retriever or SparseRetriever()
        self.fusion = fusion or RRFFusion()
        self.reranker = reranker or Reranker()

    def build_sparse_index(self, all_chunks: list[dict]) -> None:
        self.sparse_retriever.build_index(all_chunks)

    def retrieve(
        self,
        query: str,
        document_ids: list[str] | None = None,
        top_k: int | None = None,
    ) -> list[dict]:
        top_k = top_k or settings.reranker_top_k

        logger.info("Hybrid retrieval started", query=query[:50])

        dense_results = self.dense_retriever.retrieve(
            query=query,
            document_ids=document_ids,
        )

        sparse_results = self.sparse_retriever.retrieve(query=query)

        fused_results = self.fusion.fuse(dense_results, sparse_results)

        if not fused_results:
            logger.warning("No results found after fusion", query=query[:50])
            return []

        final_results = self.reranker.rerank(
            query=query,
            candidates=fused_results,
            top_k=top_k,
        )

        logger.info(
            "Hybrid retrieval complete",
            query=query[:50],
            final_count=len(final_results),
        )

        return final_results
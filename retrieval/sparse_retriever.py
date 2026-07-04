from rank_bm25 import BM25Okapi

from backend.config import get_settings
from backend.core.exceptions import RetrievalError
from backend.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class SparseRetriever:

    def __init__(self):
        self.bm25: BM25Okapi | None = None
        self.corpus_chunks: list[dict] = []

    def build_index(self, chunks: list[dict]) -> None:
        if not chunks:
            logger.warning("Empty corpus passed to BM25 indexer")
            return

        self.corpus_chunks = chunks
        tokenized_corpus = [self._tokenize(chunk["content"]) for chunk in chunks]

        try:
            self.bm25 = BM25Okapi(tokenized_corpus)
            logger.info("BM25 index built", corpus_size=len(chunks))
        except Exception as e:
            raise RetrievalError(reason=f"BM25 index build failed: {str(e)}")

    def retrieve(self, query: str, top_k: int | None = None) -> list[dict]:
        top_k = top_k or settings.retrieval_top_k_sparse

        if self.bm25 is None:
            logger.warning("BM25 index not built — returning empty results")
            return []

        try:
            tokenized_query = self._tokenize(query)
            scores = self.bm25.get_scores(tokenized_query)

            scored_chunks = list(zip(self.corpus_chunks, scores))
            scored_chunks.sort(key=lambda x: x[1], reverse=True)

            results = []
            for chunk, score in scored_chunks[:top_k]:
                if score <= 0:
                    continue
                results.append(
                    {
                        "id": chunk.get("id"),
                        "score": float(score),
                        "payload": chunk,
                    }
                )

            logger.info(
                "Sparse retrieval complete",
                query=query[:50],
                results_count=len(results),
            )

            return results

        except Exception as e:
            raise RetrievalError(reason=f"BM25 retrieval failed: {str(e)}")

    def _tokenize(self, text: str) -> list[str]:
        return text.lower().split()
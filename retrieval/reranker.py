from sentence_transformers import CrossEncoder

from backend.config import get_settings
from backend.core.exceptions import RetrievalError
from backend.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class Reranker:

    def __init__(self):
        self._model: CrossEncoder | None = None

    def _load_model(self) -> CrossEncoder:
        if self._model is None:
            logger.info("Loading reranker model", model=settings.reranker_model)
            self._model = CrossEncoder(settings.reranker_model)
            logger.info("Reranker model loaded")
        return self._model

    def rerank(
        self,
        query: str,
        candidates: list[dict],
        top_k: int | None = None,
    ) -> list[dict]:
        top_k = top_k or settings.reranker_top_k

        if not candidates:
            return []

        try:
            model = self._load_model()

            pairs = [[query, c["payload"].get("content", "")] for c in candidates]
            scores = model.predict(pairs)

            for candidate, score in zip(candidates, scores):
                candidate["rerank_score"] = float(score)

            reranked = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)
            final = reranked[:top_k]

            logger.info(
                "Reranking complete",
                query=query[:50],
                input_count=len(candidates),
                output_count=len(final),
            )

            return final

        except Exception as e:
            raise RetrievalError(reason=f"Reranking failed: {str(e)}")

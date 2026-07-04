from backend.config import get_settings
from backend.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class RRFFusion:

    def __init__(self, k: int | None = None):
        self.k = k or settings.rrf_k

    def fuse(
        self,
        dense_results: list[dict],
        sparse_results: list[dict],
    ) -> list[dict]:
        rrf_scores: dict[str, float] = {}
        chunk_data: dict[str, dict] = {}

        for rank, result in enumerate(dense_results, start=1):
            chunk_id = self._get_chunk_key(result)
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + 1.0 / (self.k + rank)
            chunk_data[chunk_id] = result

        for rank, result in enumerate(sparse_results, start=1):
            chunk_id = self._get_chunk_key(result)
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + 1.0 / (self.k + rank)
            if chunk_id not in chunk_data:
                chunk_data[chunk_id] = result

        fused = []
        for chunk_id, score in rrf_scores.items():
            entry = chunk_data[chunk_id]
            fused.append(
                {
                    "id": entry["id"],
                    "rrf_score": score,
                    "payload": entry["payload"],
                }
            )

        fused.sort(key=lambda x: x["rrf_score"], reverse=True)

        logger.info(
            "RRF fusion complete",
            dense_count=len(dense_results),
            sparse_count=len(sparse_results),
            fused_count=len(fused),
        )

        return fused

    def _get_chunk_key(self, result: dict) -> str:
        payload = result.get("payload", {})
        return payload.get("chunk_id") or str(result.get("id"))
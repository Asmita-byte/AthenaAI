from backend.core.logging import get_logger

logger = get_logger(__name__)


class EvidenceAggregator:

    def aggregate(self, tool_results: dict[str, list[dict]]) -> dict:
        text_chunks = tool_results.get("text_retriever", [])
        table_chunks = tool_results.get("table_retriever", [])
        figure_chunks = tool_results.get("figure_retriever", [])
        chart_chunks = tool_results.get("chart_retriever", [])
        metadata = tool_results.get("metadata_retriever", [])

        all_chunks = text_chunks + table_chunks + figure_chunks + chart_chunks

        deduped_chunks = self._deduplicate(all_chunks)

        evidence = {
            "text_chunks": text_chunks,
            "table_chunks": table_chunks,
            "image_chunks": figure_chunks + chart_chunks,
            "metadata": metadata,
            "all_chunks": deduped_chunks,
            "total_evidence_count": len(deduped_chunks),
        }

        logger.info(
            "Evidence aggregated",
            text_count=len(text_chunks),
            table_count=len(table_chunks),
            image_count=len(figure_chunks) + len(chart_chunks),
            total_unique=len(deduped_chunks),
        )

        return evidence

    def _deduplicate(self, chunks: list[dict]) -> list[dict]:
        seen_ids = set()
        unique_chunks = []

        for chunk in chunks:
            chunk_id = chunk.get("id")
            if chunk_id not in seen_ids:
                seen_ids.add(chunk_id)
                unique_chunks.append(chunk)

        return unique_chunks
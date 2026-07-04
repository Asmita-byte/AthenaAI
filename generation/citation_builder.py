from backend.core.logging import get_logger

logger = get_logger(__name__)


class CitationBuilder:

    def build_citations(self, context_chunks: list[dict]) -> list[dict]:
        citations = []

        for chunk in context_chunks:
            payload = chunk.get("payload", {})

            content = payload.get("content", "")
            preview = content[:150] + "..." if len(content) > 150 else content

            citation = {
                "chunk_id": payload.get("chunk_id", chunk.get("id")),
                "document_id": payload.get("document_id"),
                "source_filename": payload.get("source_filename", "unknown"),
                "chunk_type": payload.get("chunk_type", "text"),
                "page_number": payload.get("page_number"),
                "section_title": payload.get("section_title", ""),
                "content_preview": preview,
                "rerank_score": chunk.get("rerank_score"),
            }
            citations.append(citation)

        logger.info("Citations built", count=len(citations))
        return citations

    def build_evidence_summary(self, evidence: dict) -> dict:
        return {
            "text_chunks": self.build_citations(evidence.get("text_chunks", [])),
            "table_chunks": self.build_citations(evidence.get("table_chunks", [])),
            "image_chunks": self.build_citations(evidence.get("image_chunks", [])),
        }

from backend.config import get_settings
from backend.core.logging import get_logger
from ingestion.parsers.base_parser import ParsedChunk, ParsedDocument

settings = get_settings()
logger = get_logger(__name__)


class TextChunker:

    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ):
        self.chunk_size = chunk_size or settings.text_chunk_size
        self.chunk_overlap = chunk_overlap or settings.text_chunk_overlap

    def chunk_document(self, doc: ParsedDocument) -> list[ParsedChunk]:
        logger.info(
            "Chunking document",
            filename=doc.filename,
            input_text_chunks=len(doc.text_chunks),
        )

        final_chunks = []
        global_index = 0

        for parsed_chunk in doc.text_chunks:
            sub_chunks = self._split_text(parsed_chunk.content)

            for sub_text in sub_chunks:
                if not sub_text.strip():
                    continue

                final_chunks.append(
                    ParsedChunk(
                        content=sub_text.strip(),
                        chunk_type="text",
                        page_number=parsed_chunk.page_number,
                        chunk_index=global_index,
                        section_title=parsed_chunk.section_title,
                        source_filename=parsed_chunk.source_filename,
                        metadata={
                            **parsed_chunk.metadata,
                            "chunk_size": len(sub_text.split()),
                            "chunker": "text_chunker",
                        },
                    )
                )
                global_index += 1

        logger.info(
            "Chunking complete",
            filename=doc.filename,
            input_chunks=len(doc.text_chunks),
            output_chunks=len(final_chunks),
        )

        return final_chunks

    def _split_text(self, text: str) -> list[str]:
        words = text.split()

        if len(words) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(words):
            end = start + self.chunk_size
            chunk_words = words[start:end]
            chunks.append(" ".join(chunk_words))

            if end >= len(words):
                break

            start = end - self.chunk_overlap

        return chunks
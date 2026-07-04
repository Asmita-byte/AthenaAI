from backend.config import get_settings
from backend.core.logging import get_logger
from ingestion.parsers.base_parser import ParsedChunk, ParsedDocument

settings = get_settings()
logger = get_logger(__name__)


class ImageChunker:

    def chunk_document(self, doc: ParsedDocument) -> list[ParsedChunk]:
        logger.info(
            "Chunking images",
            filename=doc.filename,
            input_image_chunks=len(doc.image_chunks),
        )

        final_chunks = []
        global_index = 0

        for parsed_chunk in doc.image_chunks:
            if parsed_chunk.image is None:
                continue

            image = parsed_chunk.image
            content = self._build_content(parsed_chunk)

            final_chunks.append(
                ParsedChunk(
                    content=content,
                    chunk_type="image",
                    page_number=parsed_chunk.page_number,
                    chunk_index=global_index,
                    section_title=parsed_chunk.section_title,
                    source_filename=parsed_chunk.source_filename,
                    image=image,
                    metadata={
                        **parsed_chunk.metadata,
                        "image_path": image.image_path,
                        "image_type": image.image_type,
                        "chunker": "image_chunker",
                    },
                )
            )
            global_index += 1

        logger.info(
            "Image chunking complete",
            filename=doc.filename,
            input_chunks=len(doc.image_chunks),
            output_chunks=len(final_chunks),
        )

        return final_chunks

    def _build_content(self, parsed_chunk: ParsedChunk) -> str:
        image = parsed_chunk.image
        lines = []

        if image.caption:
            lines.append(f"Caption: {image.caption}")

        lines.append(
            f"Image from page {image.page_number}, "
            f"index {image.image_index}."
        )
        lines.append(f"Type: {image.image_type}")
        lines.append(f"Path: {image.image_path}")

        return "\n".join(lines)
from pathlib import Path

from backend.core.logging import get_logger
from ingestion.parsers.base_parser import (
    BaseParser,
    ParsedChunk,
    ParsedDocument,
)

logger = get_logger(__name__)


class TXTParser(BaseParser):

    def supported_extensions(self) -> list[str]:
        return [".txt"]

    def parse(self, file_path: Path) -> ParsedDocument:
        logger.info("Parsing TXT", filename=file_path.name)

        encodings = ["utf-8", "utf-16", "latin-1", "cp1252"]
        raw_text = None

        for encoding in encodings:
            try:
                raw_text = file_path.read_text(encoding=encoding)
                break
            except (UnicodeDecodeError, LookupError):
                continue

        if raw_text is None:
            raw_text = file_path.read_bytes().decode("utf-8", errors="replace")

        paragraphs = [p.strip() for p in raw_text.split("\n\n") if p.strip()]

        doc = ParsedDocument(
            filename=file_path.name,
            file_extension=".txt",
            total_pages=1,
            metadata={
                "total_pages": 1,
                "total_paragraphs": len(paragraphs),
                "total_chars": len(raw_text),
            },
        )

        doc.text_chunks = self._extract_text(paragraphs, file_path)

        logger.info(
            "TXT parsing complete",
            filename=file_path.name,
            summary=doc.summary(),
        )

        return doc

    def _extract_text(self, paragraphs: list[str], file_path: Path) -> list[ParsedChunk]:
        chunks = []

        for chunk_index, paragraph in enumerate(paragraphs):
            if not paragraph:
                continue

            chunks.append(
                ParsedChunk(
                    content=paragraph,
                    chunk_type="text",
                    page_number=1,
                    chunk_index=chunk_index,
                    source_filename=file_path.name,
                    metadata={"paragraph_index": chunk_index},
                )
            )

        return chunks
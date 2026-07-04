from backend.config import get_settings
from backend.core.logging import get_logger
from ingestion.parsers.base_parser import ParsedChunk, ParsedDocument

settings = get_settings()
logger = get_logger(__name__)


class TableChunker:

    def __init__(self, max_rows_per_chunk: int = 50):
        self.max_rows_per_chunk = max_rows_per_chunk

    def chunk_document(self, doc: ParsedDocument) -> list[ParsedChunk]:
        logger.info(
            "Chunking tables",
            filename=doc.filename,
            input_table_chunks=len(doc.table_chunks),
        )

        final_chunks = []
        global_index = 0

        for parsed_chunk in doc.table_chunks:
            if parsed_chunk.table is None:
                final_chunks.append(parsed_chunk)
                global_index += 1
                continue

            table = parsed_chunk.table

            if len(table.rows) <= self.max_rows_per_chunk:
                final_chunks.append(parsed_chunk)
                global_index += 1
                continue

            for batch_start in range(0, len(table.rows), self.max_rows_per_chunk):
                batch_rows = table.rows[batch_start : batch_start + self.max_rows_per_chunk]

                content_lines = []
                if table.caption:
                    content_lines.append(f"Table: {table.caption}")
                content_lines.append(f"(Rows {batch_start + 1} to {batch_start + len(batch_rows)})")
                if table.headers:
                    content_lines.append(" | ".join(table.headers))
                    content_lines.append("-" * 40)
                for row in batch_rows:
                    content_lines.append(" | ".join(str(cell) for cell in row))

                final_chunks.append(
                    ParsedChunk(
                        content="\n".join(content_lines),
                        chunk_type="table",
                        page_number=parsed_chunk.page_number,
                        chunk_index=global_index,
                        section_title=parsed_chunk.section_title,
                        source_filename=parsed_chunk.source_filename,
                        table=table,
                        metadata={
                            **parsed_chunk.metadata,
                            "batch_start": batch_start,
                            "batch_rows": len(batch_rows),
                            "chunker": "table_chunker",
                        },
                    )
                )
                global_index += 1

        logger.info(
            "Table chunking complete",
            filename=doc.filename,
            input_chunks=len(doc.table_chunks),
            output_chunks=len(final_chunks),
        )

        return final_chunks

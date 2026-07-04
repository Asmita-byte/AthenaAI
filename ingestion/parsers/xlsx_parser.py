from pathlib import Path

import pandas as pd

from backend.core.logging import get_logger
from ingestion.parsers.base_parser import (
    BaseParser,
    ParsedChunk,
    ParsedDocument,
    ParsedTable,
)

logger = get_logger(__name__)


class XLSXParser(BaseParser):

    def supported_extensions(self) -> list[str]:
        return [".xlsx", ".csv"]

    def parse(self, file_path: Path) -> ParsedDocument:
        logger.info("Parsing file", filename=file_path.name)

        doc = ParsedDocument(
            filename=file_path.name,
            file_extension=file_path.suffix.lower(),
            total_pages=1,
            metadata={},
        )

        if file_path.suffix.lower() == ".csv":
            sheets = {"Sheet1": pd.read_csv(str(file_path))}
        else:
            sheets = pd.read_excel(str(file_path), sheet_name=None)

        doc.metadata = {
            "total_sheets": len(sheets),
            "sheet_names": list(sheets.keys()),
            "total_pages": len(sheets),
        }
        doc.total_pages = len(sheets)

        doc.text_chunks = self._extract_text(sheets, file_path)
        doc.table_chunks = self._extract_tables(sheets, file_path)

        logger.info(
            "File parsing complete",
            filename=file_path.name,
            summary=doc.summary(),
        )

        return doc

    def _extract_text(self, sheets: dict, file_path: Path) -> list[ParsedChunk]:
        chunks = []
        chunk_index = 0

        for sheet_name, df in sheets.items():
            if df.empty:
                continue

            summary_lines = [
                f"Sheet: {sheet_name}",
                f"Rows: {len(df)}",
                f"Columns: {', '.join(str(c) for c in df.columns.tolist())}",
            ]

            numeric_cols = df.select_dtypes(include="number")
            if not numeric_cols.empty:
                for col in numeric_cols.columns:
                    summary_lines.append(
                        f"{col} — min: {df[col].min():.2f}, "
                        f"max: {df[col].max():.2f}, "
                        f"mean: {df[col].mean():.2f}"
                    )

            chunks.append(
                ParsedChunk(
                    content="\n".join(summary_lines),
                    chunk_type="text",
                    page_number=chunk_index + 1,
                    chunk_index=chunk_index,
                    source_filename=file_path.name,
                    section_title=sheet_name,
                    metadata={"sheet": sheet_name, "rows": len(df), "cols": len(df.columns)},
                )
            )
            chunk_index += 1

        return chunks

    def _extract_tables(self, sheets: dict, file_path: Path) -> list[ParsedChunk]:
        chunks = []
        chunk_index = 0

        for sheet_name, df in sheets.items():
            if df.empty:
                continue

            df = df.fillna("").astype(str)

            headers = df.columns.tolist()
            rows = df.values.tolist()

            max_rows = 100
            for batch_start in range(0, len(rows), max_rows):
                batch_rows = rows[batch_start : batch_start + max_rows]

                parsed_table = ParsedTable(
                    table_index=chunk_index,
                    page_number=chunk_index + 1,
                    headers=headers,
                    rows=batch_rows,
                    raw_text="",
                    caption=f"{sheet_name} (rows {batch_start + 1}-{batch_start + len(batch_rows)})",
                )

                chunks.append(
                    ParsedChunk(
                        content=parsed_table.to_text(),
                        chunk_type="table",
                        page_number=chunk_index + 1,
                        chunk_index=chunk_index,
                        source_filename=file_path.name,
                        section_title=sheet_name,
                        table=parsed_table,
                        metadata={
                            "sheet": sheet_name,
                            "batch_start": batch_start,
                            "rows_in_batch": len(batch_rows),
                        },
                    )
                )
                chunk_index += 1

        return chunks

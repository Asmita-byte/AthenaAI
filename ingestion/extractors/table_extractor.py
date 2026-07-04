from pathlib import Path

from backend.core.logging import get_logger
from ingestion.parsers.base_parser import ParsedTable

logger = get_logger(__name__)


class TableExtractor:

    def extract_from_pdf(self, file_path: Path) -> list[ParsedTable]:
        tables = []

        try:
            import pdfplumber

            with pdfplumber.open(str(file_path)) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    raw_tables = page.extract_tables()
                    if not raw_tables:
                        continue

                    for table_idx, raw_table in enumerate(raw_tables):
                        if not raw_table or len(raw_table) < 2:
                            continue

                        headers = [str(cell or "") for cell in raw_table[0]]
                        rows = [[str(cell or "") for cell in row] for row in raw_table[1:]]

                        tables.append(
                            ParsedTable(
                                table_index=table_idx,
                                page_number=page_num,
                                headers=headers,
                                rows=rows,
                                raw_text="",
                                caption=f"Table {table_idx + 1} on page {page_num}",
                            )
                        )

        except Exception as e:
            logger.warning("Table extraction failed", file=file_path.name, error=str(e))

        logger.info("Tables extracted", file=file_path.name, count=len(tables))
        return tables

    def extract_from_docx(self, file_path: Path) -> list[ParsedTable]:
        tables = []

        try:
            from docx import Document

            doc = Document(str(file_path))

            for table_idx, table in enumerate(doc.tables):
                rows_data = []
                for row in table.rows:
                    rows_data.append([cell.text.strip() for cell in row.cells])

                if not rows_data:
                    continue

                tables.append(
                    ParsedTable(
                        table_index=table_idx,
                        page_number=1,
                        headers=rows_data[0],
                        rows=rows_data[1:],
                        raw_text="",
                        caption=f"Table {table_idx + 1}",
                    )
                )

        except Exception as e:
            logger.warning("DOCX table extraction failed", file=file_path.name, error=str(e))

        logger.info("DOCX tables extracted", file=file_path.name, count=len(tables))
        return tables

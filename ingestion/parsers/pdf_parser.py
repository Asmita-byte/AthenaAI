from pathlib import Path

import fitz
import pdfplumber

from backend.config import get_settings
from backend.core.logging import get_logger
from ingestion.parsers.base_parser import (
    BaseParser,
    ParsedChunk,
    ParsedDocument,
    ParsedImage,
    ParsedTable,
)

settings = get_settings()
logger = get_logger(__name__)


class PDFParser(BaseParser):

    def supported_extensions(self) -> list[str]:
        return [".pdf"]

    def parse(self, file_path: Path) -> ParsedDocument:
        logger.info("Parsing PDF", filename=file_path.name)

        doc = ParsedDocument(
            filename=file_path.name,
            file_extension=".pdf",
            total_pages=0,
            metadata={},
        )

        doc.metadata = self._extract_metadata(file_path)
        doc.text_chunks = self._extract_text(file_path)
        doc.total_pages = doc.metadata.get("total_pages", 0)

        if self.extract_tables:
            doc.table_chunks = self._extract_tables(file_path)

        if self.extract_images:
            doc.image_chunks = self._extract_images(file_path)

        logger.info(
            "PDF parsing complete",
            filename=file_path.name,
            summary=doc.summary(),
        )

        return doc

    def _extract_metadata(self, file_path: Path) -> dict:
        metadata = {}
        with fitz.open(str(file_path)) as pdf:
            metadata["total_pages"] = pdf.page_count
            meta = pdf.metadata or {}
            metadata["title"] = meta.get("title", "")
            metadata["author"] = meta.get("author", "")
            metadata["subject"] = meta.get("subject", "")
            metadata["creator"] = meta.get("creator", "")
        return metadata

    def _extract_text(self, file_path: Path) -> list[ParsedChunk]:
        chunks = []
        chunk_index = 0

        with fitz.open(str(file_path)) as pdf:
            for page_num, page in enumerate(pdf, start=1):
                text = page.get_text("text").strip()
                if not text:
                    continue

                chunks.append(
                    ParsedChunk(
                        content=text,
                        chunk_type="text",
                        page_number=page_num,
                        chunk_index=chunk_index,
                        source_filename=file_path.name,
                        metadata={"page": page_num},
                    )
                )
                chunk_index += 1

        return chunks

    def _extract_tables(self, file_path: Path) -> list[ParsedChunk]:
        chunks = []
        chunk_index = 0

        with pdfplumber.open(str(file_path)) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                tables = page.extract_tables()
                if not tables:
                    continue

                for table_idx, raw_table in enumerate(tables):
                    if not raw_table or len(raw_table) < 2:
                        continue

                    headers = [str(cell or "") for cell in raw_table[0]]
                    rows = [[str(cell or "") for cell in row] for row in raw_table[1:]]

                    parsed_table = ParsedTable(
                        table_index=table_idx,
                        page_number=page_num,
                        headers=headers,
                        rows=rows,
                        raw_text="",
                    )

                    chunks.append(
                        ParsedChunk(
                            content=parsed_table.to_text(),
                            chunk_type="table",
                            page_number=page_num,
                            chunk_index=chunk_index,
                            source_filename=file_path.name,
                            table=parsed_table,
                            metadata={"page": page_num, "table_index": table_idx},
                        )
                    )
                    chunk_index += 1

        return chunks

    def _extract_images(self, file_path: Path) -> list[ParsedChunk]:
        chunks = []
        chunk_index = 0
        images_dir = settings.storage_images_dir

        with fitz.open(str(file_path)) as pdf:
            for page_num, page in enumerate(pdf, start=1):
                image_list = page.get_images(full=True)

                for img_idx, img_info in enumerate(image_list):
                    xref = img_info[0]
                    try:
                        base_image = pdf.extract_image(xref)
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]

                        image_filename = f"{file_path.stem}_page{page_num}_img{img_idx}.{image_ext}"
                        image_path = images_dir / image_filename

                        with open(image_path, "wb") as f:
                            f.write(image_bytes)

                        parsed_image = ParsedImage(
                            image_index=img_idx,
                            page_number=page_num,
                            image_path=str(image_path),
                            image_type="image",
                        )

                        chunks.append(
                            ParsedChunk(
                                content=f"Image extracted from page {page_num}.",
                                chunk_type="image",
                                page_number=page_num,
                                chunk_index=chunk_index,
                                source_filename=file_path.name,
                                image=parsed_image,
                                metadata={"page": page_num, "image_index": img_idx},
                            )
                        )
                        chunk_index += 1

                    except Exception as e:
                        logger.warning(
                            "Failed to extract image",
                            page=page_num,
                            img_idx=img_idx,
                            error=str(e),
                        )

        return chunks

import asyncio
from pathlib import Path

from workers.celery_app import celery_app
from backend.core.logging import get_logger, setup_logging
from backend.db.database import AsyncSessionFactory
from backend.models.document import Document
from backend.models.job import Job
from ingestion.parsers.pdf_parser import PDFParser
from ingestion.parsers.docx_parser import DOCXParser
from ingestion.parsers.pptx_parser import PPTXParser
from ingestion.parsers.xlsx_parser import XLSXParser
from ingestion.parsers.txt_parser import TXTParser
from ingestion.chunkers.text_chunker import TextChunker
from ingestion.chunkers.table_chunker import TableChunker
from ingestion.chunkers.image_chunker import ImageChunker
from embeddings.text_embedder import TextEmbedder
from embeddings.table_embedder import TableEmbedder
from embeddings.image_embedder import ImageEmbedder
from vectorstore.indexer import VectorIndexer
from datetime import datetime
from sqlalchemy import select

setup_logging()
logger = get_logger(__name__)

PARSER_MAP = {
    ".pdf": PDFParser,
    ".docx": DOCXParser,
    ".pptx": PPTXParser,
    ".xlsx": XLSXParser,
    ".csv": XLSXParser,
    ".txt": TXTParser,
}


async def _update_job_and_document(document_id: str, stage: str, progress: float, status: str = "running"):
    async with AsyncSessionFactory() as session:
        result = await session.execute(
            select(Job).where(Job.document_id == document_id).order_by(Job.created_at.desc())
        )
        job = result.scalars().first()
        if job:
            job.status = status
            job.current_stage = stage
            job.progress_percent = progress
            if status == "running" and job.started_at is None:
                job.started_at = datetime.utcnow()
            if status == "completed":
                job.completed_at = datetime.utcnow()
        await session.commit()


async def _finalize_document(document_id: str, summary: dict):
    async with AsyncSessionFactory() as session:
        document = await session.get(Document, document_id)
        if document:
            document.status = "completed"
            document.total_pages = summary["total_pages"]
            document.total_chunks = summary["total_chunks"]
            document.total_images = summary["image_chunks"]
            document.total_tables = summary["table_chunks"]
            document.has_text = summary["has_text"]
            document.has_tables = summary["has_tables"]
            document.has_images = summary["has_images"]
        await session.commit()


@celery_app.task(name="workers.tasks_ingestion.process_document", bind=True)
def process_document(self, document_id: str, file_path: str, file_extension: str) -> dict:
    logger.info("Starting document processing", document_id=document_id, file_path=file_path)

    asyncio.run(_update_job_and_document(document_id, "parsing", 10.0))

    parser_cls = PARSER_MAP.get(file_extension.lower())
    if parser_cls is None:
        asyncio.run(_update_job_and_document(document_id, "failed", 0.0, status="failed"))
        raise ValueError(f"No parser available for extension: {file_extension}")

    parser = parser_cls()
    parsed_doc = parser.parse(Path(file_path))

    asyncio.run(_update_job_and_document(document_id, "chunking", 35.0))
    text_chunks = TextChunker().chunk_document(parsed_doc)
    table_chunks = TableChunker().chunk_document(parsed_doc)
    image_chunks = ImageChunker().chunk_document(parsed_doc)

    asyncio.run(_update_job_and_document(document_id, "embedding", 60.0))
    indexer = VectorIndexer()

    if text_chunks:
        text_pairs = TextEmbedder().embed_chunks(text_chunks)
        indexer.index_text_chunks(text_pairs, document_id=document_id)

    if table_chunks:
        table_pairs = TableEmbedder().embed_table_chunks(table_chunks)
        indexer.index_text_chunks(table_pairs, document_id=document_id)

    if image_chunks:
        image_pairs = ImageEmbedder().embed_image_chunks(image_chunks)
        indexer.index_image_chunks(image_pairs, document_id=document_id)

    asyncio.run(_update_job_and_document(document_id, "indexing", 90.0))

    summary = parsed_doc.summary()
    asyncio.run(_finalize_document(document_id, summary))
    asyncio.run(_update_job_and_document(document_id, "done", 100.0, status="completed"))

    logger.info("Document processing complete", document_id=document_id, summary=summary)

    return {
        "document_id": document_id,
        "status": "completed",
        "summary": summary,
    }
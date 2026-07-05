import asyncio
from datetime import datetime
from pathlib import Path

from sqlalchemy import select

from backend.core.logging import get_logger, setup_logging
from backend.db.database import AsyncSessionFactory, engine
from backend.models.document import Document
from backend.models.job import Job
from embeddings.image_embedder import ImageEmbedder
from embeddings.table_embedder import TableEmbedder
from embeddings.text_embedder import TextEmbedder
from ingestion.chunkers.image_chunker import ImageChunker
from ingestion.chunkers.table_chunker import TableChunker
from ingestion.chunkers.text_chunker import TextChunker
from ingestion.parsers.docx_parser import DOCXParser
from ingestion.parsers.pdf_parser import PDFParser
from ingestion.parsers.pptx_parser import PPTXParser
from ingestion.parsers.txt_parser import TXTParser
from ingestion.parsers.xlsx_parser import XLSXParser
from vectorstore.indexer import VectorIndexer
from workers.celery_app import celery_app

setup_logging()
logger = get_logger(__name__)


def run_async(coro):
    """Runs an async coroutine in a fresh event loop, then disposes the
    database engine's connection pool so the next call (in a new loop)
    doesn't try to reuse connections tied to the old, closed loop."""
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    finally:
        loop.run_until_complete(engine.dispose())
        loop.close()


PARSER_MAP = {
    ".pdf": PDFParser,
    ".docx": DOCXParser,
    ".pptx": PPTXParser,
    ".xlsx": XLSXParser,
    ".csv": XLSXParser,
    ".txt": TXTParser,
}


async def _update_job_and_document(
    document_id: str, stage: str, progress: float, status: str = "running"
):
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

    run_async(_update_job_and_document(document_id, "parsing", 10.0))

    parser_cls = PARSER_MAP.get(file_extension.lower())
    if parser_cls is None:
        run_async(_update_job_and_document(document_id, "failed", 0.0, status="failed"))
        raise ValueError(f"No parser available for extension: {file_extension}")

    parser = parser_cls()
    parsed_doc = parser.parse(Path(file_path))

    run_async(_update_job_and_document(document_id, "chunking", 35.0))
    text_chunks = TextChunker().chunk_document(parsed_doc)
    table_chunks = TableChunker().chunk_document(parsed_doc)
    image_chunks = ImageChunker().chunk_document(parsed_doc)

    run_async(_update_job_and_document(document_id, "embedding", 60.0))
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

    run_async(_update_job_and_document(document_id, "indexing", 90.0))

    summary = parsed_doc.summary()
    run_async(_finalize_document(document_id, summary))
    run_async(_update_job_and_document(document_id, "done", 100.0, status="completed"))

    logger.info("Document processing complete", document_id=document_id, summary=summary)

    return {
        "document_id": document_id,
        "status": "completed",
        "summary": summary,
    }
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.logging import get_logger
from backend.models.document import Document

logger = get_logger(__name__)


class MetadataTool:

    name = "metadata_retriever"
    description = "Retrieves document-level metadata such as filenames, page counts, authors, and dates."

    async def run(self, db: AsyncSession, document_ids: list[str] | None = None) -> list[dict]:
        logger.info("MetadataTool invoked", document_ids=document_ids)

        query = select(Document)
        if document_ids:
            query = query.where(Document.id.in_(document_ids))

        result = await db.execute(query)
        documents = result.scalars().all()

        metadata_results = [
            {
                "document_id": doc.id,
                "filename": doc.original_filename,
                "title": doc.title,
                "author": doc.author,
                "total_pages": doc.total_pages,
                "total_chunks": doc.total_chunks,
                "has_text": doc.has_text,
                "has_tables": doc.has_tables,
                "has_images": doc.has_images,
            }
            for doc in documents
        ]

        logger.info("MetadataTool complete", results_count=len(metadata_results))
        return metadata_results
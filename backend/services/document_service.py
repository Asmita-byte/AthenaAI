import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.core.exceptions import DocumentNotFoundError
from backend.core.logging import get_logger
from backend.core.security import validate_upload
from backend.models.document import Document
from backend.models.job import Job

settings = get_settings()
logger = get_logger(__name__)


class DocumentService:

    async def save_upload(
        self,
        db: AsyncSession,
        filename: str,
        file_bytes: bytes,
    ) -> tuple[Document, Job]:
        validation_result = validate_upload(filename, file_bytes)

        document_id = str(uuid.uuid4())
        stored_filename = f"{document_id}{validation_result['extension']}"
        storage_path = settings.storage_raw_dir / stored_filename

        with open(storage_path, "wb") as f:
            f.write(file_bytes)

        document = Document(
            id=document_id,
            filename=stored_filename,
            original_filename=validation_result["original_filename"],
            file_extension=validation_result["extension"],
            file_size_bytes=validation_result["size_bytes"],
            mime_type=validation_result["mime_type"],
            storage_path=str(storage_path),
            status="pending",
        )
        db.add(document)
        await db.flush()

        job = Job(
            document_id=document_id,
            job_type="ingestion",
            status="pending",
        )
        db.add(job)
        await db.flush()

        logger.info(
            "Document saved and job created",
            document_id=document_id,
            job_id=job.id,
        )

        return document, job

    async def get_document(self, db: AsyncSession, document_id: str) -> Document:
        document = await db.get(Document, document_id)
        if document is None:
            raise DocumentNotFoundError(document_id=document_id)
        return document

    async def list_documents(self, db: AsyncSession) -> list[Document]:
        from sqlalchemy import select
        result = await db.execute(select(Document).order_by(Document.created_at.desc()))
        return list(result.scalars().all())

    async def link_user_document(self, db: AsyncSession, user_id: str, document_id: str) -> None:
        from backend.models.user_document import UserDocument
        link = UserDocument(user_id=user_id, document_id=document_id)
        db.add(link)
        await db.flush()

    async def list_documents_for_user(self, db: AsyncSession, user_id: str) -> list[Document]:
        from sqlalchemy import select
        from backend.models.user_document import UserDocument

        result = await db.execute(
            select(Document)
            .join(UserDocument, UserDocument.document_id == Document.id)
            .where(UserDocument.user_id == user_id)
            .order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())

    async def user_owns_document(self, db: AsyncSession, user_id: str, document_id: str) -> bool:
        from sqlalchemy import select
        from backend.models.user_document import UserDocument

        result = await db.execute(
            select(UserDocument).where(
                UserDocument.user_id == user_id,
                UserDocument.document_id == document_id,
            )
        )
        return result.scalar_one_or_none() is not None
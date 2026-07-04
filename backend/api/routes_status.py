from fastapi.responses import StreamingResponse
import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import select

from backend.api.deps import get_current_user
from backend.core.exceptions import BaseAppException, JobNotFoundError
from backend.core.logging import get_logger
from backend.dependencies import DatabaseDep
from backend.models.job import Job
from backend.models.user import User
from backend.schemas.upload import DocumentStatusResponse
from backend.services.document_service import DocumentService

logger = get_logger(__name__)
router = APIRouter(prefix="/status", tags=["Status"])

document_service = DocumentService()


@router.get("/{document_id}", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: str,
    db: DatabaseDep,
    current_user: User = Depends(get_current_user),
):
    try:
        owns = await document_service.user_owns_document(db, current_user.id, document_id)
        if not owns:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
            )

        document = await document_service.get_document(db, document_id)

        result = await db.execute(
            select(Job).where(Job.document_id == document_id).order_by(Job.created_at.desc())
        )
        job = result.scalars().first()

        if job is None:
            raise JobNotFoundError(job_id=f"for document {document_id}")

        return DocumentStatusResponse(
            document_id=document.id,
            filename=document.original_filename,
            status=job.status,
            progress_percent=job.progress_percent,
            current_stage=job.current_stage,
            error_message=job.error_message,
            total_pages=document.total_pages,
            total_chunks=document.total_chunks,
            total_images=document.total_images,
            total_tables=document.total_tables,
            has_text=document.has_text,
            has_images=document.has_images,
            has_tables=document.has_tables,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )

    except BaseAppException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"error_code": e.error_code, "message": e.message},
        )
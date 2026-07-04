from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import JSONResponse

from backend.api.deps import get_current_user
from backend.core.exceptions import BaseAppException
from backend.core.logging import get_logger
from backend.dependencies import DatabaseDep
from backend.models.user import User
from backend.schemas.upload import UploadResponse
from backend.services.document_service import DocumentService
from workers.tasks_ingestion import process_document

logger = get_logger(__name__)
router = APIRouter(prefix="/upload", tags=["Upload"])

document_service = DocumentService()


@router.post("", response_model=UploadResponse)
async def upload_document(
    db: DatabaseDep,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    try:
        file_bytes = await file.read()
        document, job = await document_service.save_upload(
            db=db,
            filename=file.filename,
            file_bytes=file_bytes,
        )

        await document_service.link_user_document(db, current_user.id, document.id)

        process_document.delay(
            document_id=document.id,
            file_path=document.storage_path,
            file_extension=document.file_extension,
        )

        return UploadResponse(
            job_id=job.id,
            document_id=document.id,
            original_filename=document.original_filename,
            sanitized_filename=document.filename,
            file_size_bytes=document.file_size_bytes,
            mime_type=document.mime_type,
            extension=document.file_extension,
            status=document.status,
            message="File uploaded successfully. Processing started.",
            created_at=document.created_at,
        )

    except BaseAppException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"error_code": e.error_code, "message": e.message},
        )
from fastapi import APIRouter, Depends

from backend.api.deps import get_current_user
from backend.dependencies import DatabaseDep
from backend.models.user import User
from backend.services.document_service import DocumentService

router = APIRouter(prefix="/me", tags=["Me"])

document_service = DocumentService()


@router.get("/documents")
async def list_my_documents(
    db: DatabaseDep,
    current_user: User = Depends(get_current_user),
):
    documents = await document_service.list_documents_for_user(db, current_user.id)
    return [
        {
            "document_id": d.id,
            "filename": d.original_filename,
            "status": d.status,
            "total_chunks": d.total_chunks,
            "created_at": d.created_at,
        }
        for d in documents
    ]
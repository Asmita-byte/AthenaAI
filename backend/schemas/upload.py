from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    job_id: str
    document_id: str
    original_filename: str
    sanitized_filename: str
    file_size_bytes: int
    mime_type: str
    extension: str
    status: str
    message: str
    created_at: datetime


class DocumentStatusResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    progress_percent: float
    current_stage: Optional[str] = None
    error_message: Optional[str] = None
    total_pages: Optional[int] = None
    total_chunks: Optional[int] = None
    total_images: Optional[int] = None
    total_tables: Optional[int] = None
    has_text: bool
    has_images: bool
    has_tables: bool
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    documents: list[DocumentStatusResponse]
    total: int
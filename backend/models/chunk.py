import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    document_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    chunk_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    char_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    image_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)

    table_rows: Mapped[int | None] = mapped_column(Integer, nullable=True)
    table_cols: Mapped[int | None] = mapped_column(Integer, nullable=True)

    qdrant_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rerank_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    section_title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    source_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    def __repr__(self) -> str:
        return (
            f"Chunk(id={self.id!r}, "
            f"document_id={self.document_id!r}, "
            f"chunk_type={self.chunk_type!r}, "
            f"page={self.page_number}, "
            f"tokens={self.token_count})"
        )
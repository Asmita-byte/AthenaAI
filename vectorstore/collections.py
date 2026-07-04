from dataclasses import dataclass


@dataclass
class TextChunkPayload:
    chunk_id: str
    document_id: str
    chunk_type: str
    content: str
    page_number: int | None
    section_title: str
    source_filename: str

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "chunk_type": self.chunk_type,
            "content": self.content,
            "page_number": self.page_number,
            "section_title": self.section_title,
            "source_filename": self.source_filename,
        }


@dataclass
class ImageChunkPayload:
    chunk_id: str
    document_id: str
    chunk_type: str
    content: str
    page_number: int | None
    image_path: str
    source_filename: str

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "chunk_type": self.chunk_type,
            "content": self.content,
            "page_number": self.page_number,
            "image_path": self.image_path,
            "source_filename": self.source_filename,
        }

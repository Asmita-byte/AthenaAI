from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ParsedTable:
    table_index: int
    page_number: int
    headers: list[str]
    rows: list[list[str]]
    raw_text: str
    caption: str = ""

    def to_text(self) -> str:
        lines = []
        if self.caption:
            lines.append(f"Table: {self.caption}")
        if self.headers:
            lines.append(" | ".join(self.headers))
            lines.append("-" * 40)
        for row in self.rows:
            lines.append(" | ".join(str(cell) for cell in row))
        return "\n".join(lines)


@dataclass
class ParsedImage:
    image_index: int
    page_number: int
    image_path: str
    caption: str = ""
    width: int = 0
    height: int = 0
    image_type: str = "image"


@dataclass
class ParsedChunk:
    content: str
    chunk_type: str
    page_number: int
    chunk_index: int
    section_title: str = ""
    source_filename: str = ""
    table: ParsedTable | None = None
    image: ParsedImage | None = None
    metadata: dict = field(default_factory=dict)

    @property
    def char_count(self) -> int:
        return len(self.content)

    @property
    def word_count(self) -> int:
        return len(self.content.split())


@dataclass
class ParsedDocument:
    filename: str
    file_extension: str
    total_pages: int
    text_chunks: list[ParsedChunk] = field(default_factory=list)
    table_chunks: list[ParsedChunk] = field(default_factory=list)
    image_chunks: list[ParsedChunk] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    @property
    def all_chunks(self) -> list[ParsedChunk]:
        return self.text_chunks + self.table_chunks + self.image_chunks

    @property
    def total_chunks(self) -> int:
        return len(self.all_chunks)

    @property
    def has_text(self) -> bool:
        return len(self.text_chunks) > 0

    @property
    def has_tables(self) -> bool:
        return len(self.table_chunks) > 0

    @property
    def has_images(self) -> bool:
        return len(self.image_chunks) > 0

    def summary(self) -> dict:
        return {
            "filename": self.filename,
            "total_pages": self.total_pages,
            "text_chunks": len(self.text_chunks),
            "table_chunks": len(self.table_chunks),
            "image_chunks": len(self.image_chunks),
            "total_chunks": self.total_chunks,
            "has_text": self.has_text,
            "has_tables": self.has_tables,
            "has_images": self.has_images,
            "metadata": self.metadata,
        }


class BaseParser(ABC):

    def __init__(self, extract_images: bool = True, extract_tables: bool = True):
        self.extract_images = extract_images
        self.extract_tables = extract_tables

    @abstractmethod
    def parse(self, file_path: Path) -> ParsedDocument:
        pass

    @abstractmethod
    def supported_extensions(self) -> list[str]:
        pass

    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.supported_extensions()
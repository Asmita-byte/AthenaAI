import pytest
from ingestion.chunkers.text_chunker import TextChunker
from ingestion.chunkers.table_chunker import TableChunker
from ingestion.parsers.base_parser import ParsedChunk, ParsedDocument, ParsedTable


def make_text_chunk(content: str, page: int = 1, index: int = 0) -> ParsedChunk:
    return ParsedChunk(
        content=content,
        chunk_type="text",
        page_number=page,
        chunk_index=index,
        source_filename="test.txt",
    )


def make_doc_with_text(chunks: list[ParsedChunk]) -> ParsedDocument:
    doc = ParsedDocument(
        filename="test.txt",
        file_extension=".txt",
        total_pages=1,
    )
    doc.text_chunks = chunks
    return doc


class TestTextChunker:

    def test_short_text_no_split(self):
        chunker = TextChunker(chunk_size=512, chunk_overlap=50)
        chunk = make_text_chunk("Short text that fits in one chunk.")
        doc = make_doc_with_text([chunk])
        result = chunker.chunk_document(doc)

        assert len(result) == 1
        assert result[0].content == "Short text that fits in one chunk."

    def test_long_text_splits(self):
        long_text = " ".join([f"word{i}" for i in range(600)])
        chunker = TextChunker(chunk_size=512, chunk_overlap=50)
        chunk = make_text_chunk(long_text)
        doc = make_doc_with_text([chunk])
        result = chunker.chunk_document(doc)

        assert len(result) > 1
        for r in result:
            assert len(r.content.split()) <= 512

    def test_overlap_preserved(self):
        words = [f"w{i}" for i in range(600)]
        long_text = " ".join(words)
        chunker = TextChunker(chunk_size=100, chunk_overlap=20)
        chunk = make_text_chunk(long_text)
        doc = make_doc_with_text([chunk])
        result = chunker.chunk_document(doc)

        assert len(result) > 1
        first_end = result[0].content.split()[-20:]
        second_start = result[1].content.split()[:20]
        assert first_end == second_start

    def test_empty_content_skipped(self):
        chunker = TextChunker()
        chunk = make_text_chunk("   ")
        doc = make_doc_with_text([chunk])
        result = chunker.chunk_document(doc)
        assert len(result) == 0

    def test_preserves_metadata(self):
        chunker = TextChunker(chunk_size=512)
        chunk = make_text_chunk("Some content.", page=5)
        chunk.section_title = "Introduction"
        doc = make_doc_with_text([chunk])
        result = chunker.chunk_document(doc)

        assert result[0].page_number == 5
        assert result[0].section_title == "Introduction"


class TestTableChunker:

    def test_small_table_no_split(self):
        table = ParsedTable(
            table_index=0,
            page_number=1,
            headers=["Col1", "Col2"],
            rows=[["A", "B"], ["C", "D"]],
            raw_text="",
        )
        chunk = ParsedChunk(
            content=table.to_text(),
            chunk_type="table",
            page_number=1,
            chunk_index=0,
            source_filename="test.pdf",
            table=table,
        )
        doc = ParsedDocument(filename="test.pdf", file_extension=".pdf", total_pages=1)
        doc.table_chunks = [chunk]

        chunker = TableChunker(max_rows_per_chunk=50)
        result = chunker.chunk_document(doc)

        assert len(result) == 1

    def test_large_table_splits(self):
        table = ParsedTable(
            table_index=0,
            page_number=1,
            headers=["Col1", "Col2"],
            rows=[[f"row{i}", f"val{i}"] for i in range(120)],
            raw_text="",
        )
        chunk = ParsedChunk(
            content=table.to_text(),
            chunk_type="table",
            page_number=1,
            chunk_index=0,
            source_filename="test.pdf",
            table=table,
        )
        doc = ParsedDocument(filename="test.pdf", file_extension=".pdf", total_pages=1)
        doc.table_chunks = [chunk]

        chunker = TableChunker(max_rows_per_chunk=50)
        result = chunker.chunk_document(doc)

        assert len(result) == 3
import os
import tempfile
import pytest
from pathlib import Path

from ingestion.parsers.txt_parser import TXTParser
from ingestion.chunkers.text_chunker import TextChunker
from embeddings.text_embedder import TextEmbedder


class TestIngestionPipeline:

    def test_txt_parse_chunk_embed_pipeline(self):
        content = "\n\n".join([
            f"This is paragraph {i} with some meaningful content about topic {i}."
            for i in range(5)
        ])
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        )
        tmp.write(content)
        tmp.close()
        path = Path(tmp.name)

        try:
            parser = TXTParser()
            doc = parser.parse(path)
            assert len(doc.text_chunks) == 5

            chunker = TextChunker(chunk_size=512, chunk_overlap=50)
            chunks = chunker.chunk_document(doc)
            assert len(chunks) >= 5

            embedder = TextEmbedder()
            pairs = embedder.embed_chunks(chunks)
            assert len(pairs) == len(chunks)
            assert all(len(vec) == 384 for _, vec in pairs)

        finally:
            os.unlink(path)

    def test_pipeline_preserves_source_filename(self):
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        )
        tmp.write("Test content paragraph one.\n\nTest content paragraph two.")
        tmp.close()
        path = Path(tmp.name)

        try:
            parser = TXTParser()
            doc = parser.parse(path)
            chunker = TextChunker()
            chunks = chunker.chunk_document(doc)

            for chunk in chunks:
                assert chunk.source_filename == path.name

        finally:
            os.unlink(path)
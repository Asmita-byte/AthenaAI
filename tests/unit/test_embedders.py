from unittest.mock import MagicMock, patch

import pytest

from ingestion.parsers.base_parser import ParsedChunk


class TestTextEmbedder:

    def test_embed_text_returns_vector(self):
        from embeddings.text_embedder import TextEmbedder

        embedder = TextEmbedder()
        vec = embedder.embed_text("This is a test sentence.")

        assert isinstance(vec, list)
        assert len(vec) == 384
        assert all(isinstance(v, float) for v in vec)

    def test_embed_empty_text_raises(self):
        from backend.core.exceptions import EmbeddingError
        from embeddings.text_embedder import TextEmbedder

        embedder = TextEmbedder()

        with pytest.raises(EmbeddingError):
            embedder.embed_text("")

    def test_embed_batch_returns_correct_count(self):
        from embeddings.text_embedder import TextEmbedder

        embedder = TextEmbedder()
        texts = ["Hello", "World", "Test sentence"]
        result = embedder.embed_batch(texts)

        assert len(result) == 3
        assert all(len(v) == 384 for v in result)

    def test_embed_chunks(self):
        from embeddings.text_embedder import TextEmbedder

        embedder = TextEmbedder()

        chunks = [
            ParsedChunk(
                content="First chunk content",
                chunk_type="text",
                page_number=1,
                chunk_index=0,
                source_filename="test.pdf",
            ),
            ParsedChunk(
                content="Second chunk content",
                chunk_type="text",
                page_number=2,
                chunk_index=1,
                source_filename="test.pdf",
            ),
        ]

        result = embedder.embed_chunks(chunks)
        assert len(result) == 2
        assert result[0][0] == chunks[0]
        assert len(result[0][1]) == 384


class TestTableEmbedder:

    def test_embed_table_content(self):
        from embeddings.table_embedder import TableEmbedder

        embedder = TableEmbedder()
        vec = embedder.embed_table("Year | Revenue\n2023 | $394B")

        assert isinstance(vec, list)
        assert len(vec) == 384

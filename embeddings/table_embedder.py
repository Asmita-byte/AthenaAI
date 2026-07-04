from backend.core.logging import get_logger
from embeddings.text_embedder import TextEmbedder

logger = get_logger(__name__)


class TableEmbedder:

    def __init__(self, text_embedder: TextEmbedder | None = None):
        self.text_embedder = text_embedder or TextEmbedder()

    def embed_table(self, table_content: str) -> list[float]:
        return self.text_embedder.embed_text(table_content)

    def embed_tables_batch(self, table_contents: list[str]) -> list[list[float]]:
        logger.info("Embedding table batch", count=len(table_contents))
        return self.text_embedder.embed_batch(table_contents)

    def embed_table_chunks(self, chunks: list) -> list[tuple]:
        if not chunks:
            return []

        texts = [chunk.content for chunk in chunks]
        embeddings = self.embed_tables_batch(texts)

        logger.info("Table chunks embedded", count=len(chunks))
        return list(zip(chunks, embeddings))

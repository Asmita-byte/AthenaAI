import pytest
from retrieval.fusion import RRFFusion
from retrieval.sparse_retriever import SparseRetriever


class TestRRFFusion:

    def make_result(self, chunk_id: str, score: float) -> dict:
        return {
            "id": chunk_id,
            "score": score,
            "payload": {"chunk_id": chunk_id, "content": f"Content for {chunk_id}"},
        }

    def test_fuse_combines_results(self):
        fusion = RRFFusion(k=60)
        dense = [self.make_result("chunk_a", 0.9), self.make_result("chunk_b", 0.8)]
        sparse = [self.make_result("chunk_b", 0.85), self.make_result("chunk_c", 0.7)]

        result = fusion.fuse(dense, sparse)
        ids = [r["payload"]["chunk_id"] for r in result]

        assert "chunk_a" in ids
        assert "chunk_b" in ids
        assert "chunk_c" in ids

    def test_common_chunk_gets_higher_score(self):
        fusion = RRFFusion(k=60)
        dense = [self.make_result("chunk_a", 0.9), self.make_result("chunk_b", 0.8)]
        sparse = [self.make_result("chunk_a", 0.85), self.make_result("chunk_c", 0.7)]

        result = fusion.fuse(dense, sparse)
        top = result[0]["payload"]["chunk_id"]
        assert top == "chunk_a"

    def test_empty_results(self):
        fusion = RRFFusion(k=60)
        result = fusion.fuse([], [])
        assert result == []

    def test_rrf_score_formula(self):
        fusion = RRFFusion(k=60)
        dense = [self.make_result("only_chunk", 0.9)]
        sparse = []

        result = fusion.fuse(dense, sparse)
        expected_score = 1.0 / (60 + 1)
        assert abs(result[0]["rrf_score"] - expected_score) < 0.0001


class TestSparseRetriever:

    def test_build_and_retrieve(self):
        retriever = SparseRetriever()
        corpus = [
            {"id": "1", "content": "Apple revenue was 394 billion in 2023"},
            {"id": "2", "content": "Google announced new AI features"},
            {"id": "3", "content": "Apple launched new iPhone models"},
        ]
        retriever.build_index(corpus)
        results = retriever.retrieve("Apple revenue", top_k=2)

        assert len(results) <= 2
        result_ids = [r["payload"]["id"] for r in results]
        assert "1" in result_ids

    def test_empty_corpus(self):
        retriever = SparseRetriever()
        retriever.build_index([])
        results = retriever.retrieve("test query")
        assert results == []

    def test_no_match_returns_empty(self):
        retriever = SparseRetriever()
        corpus = [{"id": "1", "content": "completely unrelated content"}]
        retriever.build_index(corpus)
        results = retriever.retrieve("xyzzy quantum physics 99999")
        assert len(results) == 0
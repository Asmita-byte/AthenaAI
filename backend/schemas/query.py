from typing import Any, Optional

from pydantic import BaseModel, Field


class CitationModel(BaseModel):
    chunk_id: str
    document_id: str
    source_filename: str
    chunk_type: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    content_preview: str
    rerank_score: Optional[float] = None


class EvidenceModel(BaseModel):
    text_chunks: list[CitationModel] = []
    table_chunks: list[CitationModel] = []
    image_chunks: list[CitationModel] = []


class LatencyModel(BaseModel):
    retrieval_ms: Optional[float] = None
    reranking_ms: Optional[float] = None
    generation_ms: Optional[float] = None
    total_ms: Optional[float] = None


class QueryRequest(BaseModel):
    query: str = Field(
        min_length=1, max_length=2000, description="User question to ask against the documents"
    )
    document_ids: Optional[list[str]] = Field(
        default=None, description="Specific document IDs to query. If None, queries all documents."
    )
    session_id: Optional[str] = Field(
        default=None, description="Chat session ID for conversation history"
    )
    top_k: int = Field(
        default=8, ge=1, le=20, description="Number of chunks to use for answer generation"
    )
    include_evidence: bool = Field(
        default=True, description="Include retrieved evidence chunks in response"
    )


class QueryResponse(BaseModel):
    answer: str
    session_id: str
    citations: list[CitationModel] = []
    evidence: Optional[EvidenceModel] = None
    latency: LatencyModel
    llm_provider: str
    llm_model: str
    chunks_retrieved: int
    chunks_after_rerank: int

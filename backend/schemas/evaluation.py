from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class EvaluationRequest(BaseModel):
    session_id: Optional[str] = None
    document_ids: Optional[list[str]] = None
    sample_size: int = 10


class MetricScore(BaseModel):
    name: str
    score: float
    description: str


class EvaluationResponse(BaseModel):
    evaluation_id: str
    status: str
    metrics: list[MetricScore] = []
    overall_score: float
    total_questions: int
    created_at: datetime
    report_path: Optional[str] = None
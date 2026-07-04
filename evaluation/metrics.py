from dataclasses import dataclass

from backend.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class EvalMetric:
    name: str
    score: float
    description: str


def compute_answer_relevancy(query: str, answer: str) -> EvalMetric:
    query_words = set(query.lower().split())
    answer_words = set(answer.lower().split())
    overlap = len(query_words & answer_words)
    score = min(overlap / max(len(query_words), 1), 1.0)

    return EvalMetric(
        name="answer_relevancy",
        score=round(score, 4),
        description="Measures overlap between query keywords and answer.",
    )


def compute_faithfulness(answer: str, context_chunks: list[dict]) -> EvalMetric:
    if not context_chunks:
        return EvalMetric(name="faithfulness", score=0.0, description="No context provided.")

    context_text = " ".join(c.get("payload", {}).get("content", "") for c in context_chunks).lower()

    answer_words = [w for w in answer.lower().split() if len(w) > 4]
    if not answer_words:
        return EvalMetric(
            name="faithfulness", score=1.0, description="No significant words to check."
        )

    grounded = sum(1 for w in answer_words if w in context_text)
    score = grounded / len(answer_words)

    return EvalMetric(
        name="faithfulness",
        score=round(score, 4),
        description="Fraction of answer words found in retrieved context.",
    )


def compute_context_utilization(context_chunks: list[dict], top_k: int) -> EvalMetric:
    used = len(context_chunks)
    score = min(used / max(top_k, 1), 1.0)

    return EvalMetric(
        name="context_utilization",
        score=round(score, 4),
        description="Fraction of top_k context chunks that were used.",
    )

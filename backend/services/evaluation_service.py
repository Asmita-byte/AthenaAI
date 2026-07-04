from backend.core.logging import get_logger
from evaluation.metrics import (
    compute_answer_relevancy,
    compute_context_utilization,
    compute_faithfulness,
)
from evaluation.report_generator import ReportGenerator

logger = get_logger(__name__)


class EvaluationService:

    async def run_evaluation(
        self,
        sample_size: int = 10,
        samples: list[dict] | None = None,
    ) -> dict:
        logger.info("Evaluation started", sample_size=sample_size)

        if not samples:
            return {
                "status": "no_samples",
                "message": "No evaluation samples provided. Run queries first.",
            }

        all_metrics = []
        generator = ReportGenerator()

        for sample in samples[:sample_size]:
            query = sample.get("query", "")
            answer = sample.get("answer", "")
            context_chunks = sample.get("context_chunks", [])

            relevancy = compute_answer_relevancy(query, answer)
            faithfulness = compute_faithfulness(answer, context_chunks)
            utilization = compute_context_utilization(context_chunks, top_k=8)

            all_metrics.append(
                {
                    "query": query[:100],
                    "answer_relevancy": relevancy.score,
                    "faithfulness": faithfulness.score,
                    "context_utilization": utilization.score,
                }
            )

        avg_relevancy = sum(m["answer_relevancy"] for m in all_metrics) / len(all_metrics)
        avg_faithfulness = sum(m["faithfulness"] for m in all_metrics) / len(all_metrics)

        report_path = generator.generate(all_metrics)

        return {
            "status": "completed",
            "total_samples": len(all_metrics),
            "avg_answer_relevancy": round(avg_relevancy, 4),
            "avg_faithfulness": round(avg_faithfulness, 4),
            "report_path": report_path,
        }

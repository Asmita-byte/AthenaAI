from backend.core.logging import get_logger

logger = get_logger(__name__)


class RagasEvaluator:

    def evaluate(self, samples: list[dict]) -> dict:
        logger.info("Ragas evaluation started", sample_count=len(samples))

        try:
            from datasets import Dataset
            from ragas import evaluate
            from ragas.metrics import answer_relevancy, context_recall, faithfulness

            dataset = Dataset.from_list(
                [
                    {
                        "question": s["query"],
                        "answer": s["answer"],
                        "contexts": [
                            c.get("payload", {}).get("content", "")
                            for c in s.get("context_chunks", [])
                        ],
                        "ground_truth": s.get("ground_truth", ""),
                    }
                    for s in samples
                ]
            )

            result = evaluate(dataset, metrics=[faithfulness, answer_relevancy, context_recall])
            scores = result.to_pandas().mean().to_dict()

            logger.info("Ragas evaluation complete", scores=scores)
            return scores

        except Exception as e:
            logger.warning("Ragas evaluation failed", error=str(e))
            return {"error": str(e), "status": "ragas_unavailable"}

from backend.core.logging import get_logger

logger = get_logger(__name__)


class DeepEvalEvaluator:

    def evaluate(self, query: str, answer: str, context_chunks: list[dict]) -> dict:
        logger.info("DeepEval evaluation started")

        try:
            from deepeval import evaluate
            from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
            from deepeval.test_case import LLMTestCase

            context = [c.get("payload", {}).get("content", "") for c in context_chunks]

            test_case = LLMTestCase(
                input=query,
                actual_output=answer,
                retrieval_context=context,
            )

            relevancy = AnswerRelevancyMetric(threshold=0.5)
            faithfulness = FaithfulnessMetric(threshold=0.5)

            evaluate([test_case], [relevancy, faithfulness])

            return {
                "answer_relevancy": relevancy.score,
                "faithfulness": faithfulness.score,
            }

        except Exception as e:
            logger.warning("DeepEval evaluation failed", error=str(e))
            return {"error": str(e), "status": "deepeval_unavailable"}

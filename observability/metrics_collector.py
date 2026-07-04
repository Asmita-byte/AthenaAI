from dataclasses import dataclass, field
from datetime import datetime

from backend.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class QueryMetric:
    query: str
    session_id: str
    latency_ms: float
    chunks_retrieved: int
    llm_provider: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


class MetricsCollector:

    def __init__(self):
        self._query_metrics: list[QueryMetric] = []
        self._ingestion_metrics: list[dict] = []

    def record_query(
        self,
        query: str,
        session_id: str,
        latency_ms: float,
        chunks_retrieved: int,
        llm_provider: str,
    ) -> None:
        metric = QueryMetric(
            query=query,
            session_id=session_id,
            latency_ms=latency_ms,
            chunks_retrieved=chunks_retrieved,
            llm_provider=llm_provider,
        )
        self._query_metrics.append(metric)
        logger.info(
            "Query metric recorded",
            session_id=session_id,
            latency_ms=round(latency_ms, 2),
            provider=llm_provider,
        )

    def record_ingestion(self, document_id: str, duration_ms: float, summary: dict) -> None:
        self._ingestion_metrics.append(
            {
                "document_id": document_id,
                "duration_ms": round(duration_ms, 2),
                "summary": summary,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        logger.info(
            "Ingestion metric recorded",
            document_id=document_id,
            duration_ms=round(duration_ms, 2),
        )

    def get_query_stats(self) -> dict:
        if not self._query_metrics:
            return {"total_queries": 0}

        latencies = [m.latency_ms for m in self._query_metrics]
        return {
            "total_queries": len(self._query_metrics),
            "avg_latency_ms": round(sum(latencies) / len(latencies), 2),
            "min_latency_ms": round(min(latencies), 2),
            "max_latency_ms": round(max(latencies), 2),
        }

    def get_ingestion_stats(self) -> dict:
        if not self._ingestion_metrics:
            return {"total_documents": 0}

        durations = [m["duration_ms"] for m in self._ingestion_metrics]
        return {
            "total_documents": len(self._ingestion_metrics),
            "avg_duration_ms": round(sum(durations) / len(durations), 2),
        }

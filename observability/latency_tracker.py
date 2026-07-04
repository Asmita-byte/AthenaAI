import time
from contextlib import contextmanager
from dataclasses import dataclass, field

from backend.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class LatencyRecord:
    stage: str
    duration_ms: float


@dataclass
class RequestLatency:
    request_id: str
    records: list[LatencyRecord] = field(default_factory=list)

    def add(self, stage: str, duration_ms: float) -> None:
        self.records.append(LatencyRecord(stage=stage, duration_ms=duration_ms))

    def total_ms(self) -> float:
        return sum(r.duration_ms for r in self.records)

    def to_dict(self) -> dict:
        result = {r.stage: round(r.duration_ms, 2) for r in self.records}
        result["total_ms"] = round(self.total_ms(), 2)
        return result


class LatencyTracker:

    def __init__(self, request_id: str):
        self.latency = RequestLatency(request_id=request_id)

    @contextmanager
    def track(self, stage: str):
        start = time.perf_counter()
        try:
            yield
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            self.latency.add(stage, duration_ms)
            logger.debug(
                "Stage latency recorded",
                stage=stage,
                duration_ms=round(duration_ms, 2),
            )

    def get_summary(self) -> dict:
        return self.latency.to_dict()

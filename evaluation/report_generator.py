import json
from datetime import datetime
from pathlib import Path

from backend.config import get_settings
from backend.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class ReportGenerator:

    def generate(self, metrics: list[dict], metadata: dict | None = None) -> str:
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
            "metrics": metrics,
        }

        report_path = (
            settings.eval_results_dir / f"eval_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        )

        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info("Evaluation report generated", path=str(report_path))
        return str(report_path)

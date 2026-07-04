from backend.core.logging import get_logger

logger = get_logger(__name__)


def setup_otel() -> None:
    logger.info(
        "OpenTelemetry setup placeholder — integrate with OTel SDK in production",
    )

from workers.celery_app import celery_app
from backend.core.logging import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


@celery_app.task(name="workers.tasks_graph.build_document_graph")
def build_document_graph(document_id: str) -> dict:
    logger.info("Knowledge graph task placeholder invoked", document_id=document_id)

    return {
        "document_id": document_id,
        "status": "pending_kg_implementation",
    }
from celery import Celery

from backend.config import get_settings

settings = get_settings()

celery_app = Celery(
    "multimodal_doc_intelligence",
    broker=settings.effective_celery_broker,
    backend=settings.effective_celery_backend,
    include=[
        "workers.tasks_ingestion",
        "workers.tasks_captioning",
        "workers.tasks_graph",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,
    worker_prefetch_multiplier=1,
)

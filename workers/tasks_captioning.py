from backend.core.logging import get_logger, setup_logging
from workers.celery_app import celery_app

setup_logging()
logger = get_logger(__name__)


@celery_app.task(name="workers.tasks_captioning.caption_image")
def caption_image(image_path: str) -> dict:
    logger.info("Captioning task placeholder invoked", image_path=image_path)

    return {
        "image_path": image_path,
        "caption": "",
        "status": "pending_vlm_implementation",
    }

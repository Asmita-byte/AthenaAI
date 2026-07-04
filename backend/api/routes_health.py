from fastapi import APIRouter

from backend.config import get_settings
from vectorstore.qdrant_client import get_collection_info

settings = get_settings()
router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/detailed")
async def detailed_health_check():
    checks = {"app": "healthy"}

    try:
        info = get_collection_info(settings.qdrant_text_collection)
        checks["qdrant"] = "healthy"
        checks["text_collection_count"] = info["vectors_count"]
    except Exception as e:
        checks["qdrant"] = f"unhealthy: {str(e)}"

    return checks
from backend.api.routes_evaluation import router as evaluation_router
from backend.api.routes_health import router as health_router
from backend.api.routes_query import router as query_router
from backend.api.routes_status import router as status_router
from backend.api.routes_upload import router as upload_router

__all__ = [
    "upload_router",
    "query_router",
    "status_router",
    "health_router",
    "evaluation_router",
]

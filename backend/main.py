from contextlib import asynccontextmanager
from typing import AsyncGenerator

from vectorstore.qdrant_client import ensure_collections

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.core.logging import get_logger, setup_logging
from backend.db.database import init_db

from backend.api import routes_health, routes_upload, routes_query, routes_status, routes_evaluation, routes_auth, routes_me
from backend.models.user import User

from backend.models.user_document import UserDocument  # noqa: F401
from backend.models.user_session import UserSession  # noqa: F401

settings = get_settings()
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting up application", app=settings.app_name, version=settings.app_version)
    settings.ensure_directories()
    await init_db()
    ensure_collections()
    logger.info("Application startup complete")
    yield
    logger.info("Shutting down application")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Production-grade Multimodal RAG Platform",
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    # allow_origins=settings.allowed_origins,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(routes_health.router)
app.include_router(routes_upload.router)
app.include_router(routes_query.router)
app.include_router(routes_status.router)
app.include_router(routes_evaluation.router)
app.include_router(routes_auth.router)
app.include_router(routes_me.router)


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }


@app.get("/", tags=["Root"])
async def root() -> dict:
    return {
        "message": f"Welcome to {settings.app_name}",
        "docs": "/docs",
        "health": "/health",
    }
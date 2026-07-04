from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).parent.parent


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="Multimodal Document Intelligence Platform")
    app_version: str = Field(default="0.1.0")
    debug: bool = Field(default=False)
    environment: str = Field(default="development")

    # API Server
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    allowed_origins: List[str] = Field(default=["http://localhost:8501", "http://127.0.0.1:8501"])

    # Storage
    storage_raw_dir: Path = Field(default=PROJECT_ROOT / "storage" / "raw")
    storage_images_dir: Path = Field(default=PROJECT_ROOT / "storage" / "images")
    storage_graphs_dir: Path = Field(default=PROJECT_ROOT / "storage" / "graphs")
    max_upload_size_bytes: int = Field(default=50 * 1024 * 1024)
    allowed_extensions: List[str] = Field(
        default=[
            ".pdf",
            ".docx",
            ".pptx",
            ".xlsx",
            ".csv",
            ".txt",
            ".png",
            ".jpg",
            ".jpeg",
            ".webp",
        ]
    )

    # Database
    database_url: str = Field(default=f"sqlite+aiosqlite:///{PROJECT_ROOT}/storage/metadata.db")

    # Redis
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_db: int = Field(default=0)

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # Celery
    celery_broker_url: Optional[str] = Field(default=None)
    celery_result_backend: Optional[str] = Field(default=None)

    @property
    def effective_celery_broker(self) -> str:
        return self.celery_broker_url or self.redis_url

    @property
    def effective_celery_backend(self) -> str:
        return self.celery_result_backend or self.redis_url

    # Qdrant
    qdrant_host: str = Field(default="localhost")
    qdrant_port: int = Field(default=6333)
    qdrant_use_memory: bool = Field(default=False)
    qdrant_persist_dir: Path = Field(default=PROJECT_ROOT / "storage" / "qdrant")
    qdrant_text_collection: str = Field(default="text_chunks")
    qdrant_image_collection: str = Field(default="image_chunks")

    # Embeddings
    text_embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    text_embedding_dim: int = Field(default=384)
    image_embedding_model: str = Field(default="openai/clip-vit-base-patch32")
    image_embedding_dim: int = Field(default=512)

    # Reranker
    reranker_model: str = Field(default="cross-encoder/ms-marco-MiniLM-L-6-v2")
    reranker_top_k: int = Field(default=8)

    # LLMs
    groq_api_key: Optional[str] = Field(default=None)
    groq_model: str = Field(default="llama-3.3-70b-versatile")
    gemini_api_key: Optional[str] = Field(default=None)
    gemini_model: str = Field(default="gemini-1.5-flash")
    vlm_model: str = Field(default="Qwen/Qwen2-VL-7B-Instruct")
    use_vlm_captioning: bool = Field(default=True)

    # Chunking
    text_chunk_size: int = Field(default=512)
    text_chunk_overlap: int = Field(default=50)

    # Retrieval
    retrieval_top_k_dense: int = Field(default=20)
    retrieval_top_k_sparse: int = Field(default=20)
    rrf_k: int = Field(default=60)

    # Cache TTLs
    embedding_cache_ttl: int = Field(default=3600)
    query_cache_ttl: int = Field(default=900)

    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")

    # Evaluation
    openai_api_key: Optional[str] = Field(default=None)
    eval_results_dir: Path = Field(default=PROJECT_ROOT / "storage" / "eval_results")

    # Auth
    jwt_secret_key: str = Field(default="CHANGE_THIS_IN_PRODUCTION")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=60 * 24)  # 1 day

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        valid = {"development", "staging", "production"}
        if value.lower() not in valid:
            raise ValueError(f"environment must be one of {valid}, got: {value}")
        return value.lower()

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = value.upper()
        if upper not in valid:
            raise ValueError(f"log_level must be one of {valid}, got: {value}")
        return upper

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    def ensure_directories(self) -> None:
        dirs = [
            self.storage_raw_dir,
            self.storage_images_dir,
            self.storage_graphs_dir,
            self.qdrant_persist_dir,
            self.eval_results_dir,
        ]
        for directory in dirs:
            directory.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

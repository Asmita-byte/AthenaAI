from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from backend.config import get_settings
from backend.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


_connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

engine = create_async_engine(
    url=settings.database_url,
    echo=settings.debug,
    connect_args=_connect_args,
)

AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Lightweight, idempotent migration: adds the user_id column to an
        # already-existing chat_messages table (create_all only creates NEW
        # tables/columns for brand new tables, it never alters existing ones).
        # Safe to run on every startup — no-ops if the column already exists.
        if not settings.database_url.startswith("sqlite"):
            await conn.execute(
                text("ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS user_id VARCHAR(36)")
            )
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_chat_messages_user_id "
                    "ON chat_messages (user_id)"
                )
            )

    logger.info("Database initialized", database_url=settings.database_url)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

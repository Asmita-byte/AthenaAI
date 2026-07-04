import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.config import get_settings
from backend.db.database import Base, get_db_session
from backend.main import app

settings = get_settings()

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_metadata.db"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionFactory = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def override_get_db():
    async with TestSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


app.dependency_overrides[get_db_session] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def client(setup_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session(setup_db):
    async with TestSessionFactory() as session:
        yield session


@pytest_asyncio.fixture(scope="session")
async def auth_token(setup_db):
    """Creates one test user for the whole test session and returns a valid JWT."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        signup_payload = {
            "email": "testuser@example.com",
            "password": "testpassword123",
            "full_name": "Test User",
        }
        await ac.post("/auth/signup", json=signup_payload)  # ignore if already exists

        login_resp = await ac.post(
            "/auth/login",
            json={"email": signup_payload["email"], "password": signup_payload["password"]},
        )
        return login_resp.json()["access_token"]


@pytest_asyncio.fixture
async def auth_headers(auth_token):
    """Ready-to-use Authorization header for hitting protected routes in tests."""
    return {"Authorization": f"Bearer {auth_token}"}

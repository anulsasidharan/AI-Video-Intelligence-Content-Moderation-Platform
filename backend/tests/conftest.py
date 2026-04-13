"""
Shared test fixtures.

Uses an in-memory SQLite database (via aiosqlite) so tests run without a
running PostgreSQL or Redis instance. Redis is mocked via fakeredis.
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.models  # noqa: F401 — register all SQLAlchemy tables on metadata
from app.dependencies import get_db, get_redis
from app.main import app
from app.models.base import Base

# ── In-memory SQLite engine for tests ────────────────────────────────────────

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine):
    factory = async_sessionmaker(bind=db_engine, expire_on_commit=False, autoflush=True)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def redis_client():
    """Fake async Redis client."""
    try:
        import fakeredis.aioredis as fakeredis

        client = fakeredis.FakeRedis(decode_responses=True)
        yield client
        await client.aclose()
    except ImportError:
        pytest.skip("fakeredis not installed — skipping Redis-dependent tests")


@pytest_asyncio.fixture(scope="function")
async def client(db_session, redis_client):
    """AsyncClient with overridden DB and Redis dependencies."""

    async def _get_db():
        yield db_session

    async def _get_redis():
        yield redis_client

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_redis] = _get_redis

    # Patch the module-level Redis singleton used by RateLimitMiddleware so that
    # rate limit counters are isolated per test (fresh fakeredis instance each time).
    import app.dependencies as _deps

    _original_redis = _deps._redis
    _deps._redis = redis_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    _deps._redis = _original_redis


@pytest_asyncio.fixture(scope="function")
async def admin_token(client: AsyncClient, db_session: AsyncSession) -> str:
    """Register a user, promote to ADMIN in DB, and return a fresh access token."""
    import uuid

    from sqlalchemy import update

    from app.models.user import User, UserRole

    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Test Admin",
            "email": "testadmin@vidshield.ai",
            "password": "adminpass123",
        },
    )
    user_id = uuid.UUID(resp.json()["data"]["user"]["id"])

    await db_session.execute(update(User).where(User.id == user_id).values(role=UserRole.ADMIN))
    await db_session.commit()

    # Re-login to get a token (role is read from DB on each request so same token works,
    # but re-login is cleaner for test clarity)
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "testadmin@vidshield.ai", "password": "adminpass123"},
    )
    return login.json()["data"]["access_token"]

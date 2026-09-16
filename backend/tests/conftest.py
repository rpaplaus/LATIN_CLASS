from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.api.deps import get_db
from app.core.config import settings
from app.core.security import get_password_hash
from app.main import app
from app.models.user import User

# Test engine with NullPool prevents cross-event-loop connection reuse in pytest
test_engine = create_async_engine(
    settings.async_database_url,
    poolclass=NullPool,
    future=True,
    echo=False,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a scoped clean database session for tests with automatic cleanup."""
    async with TestingSessionLocal() as session:
        yield session
        # Truncate tables to ensure complete test isolation
        await session.execute(text("TRUNCATE TABLE users CASCADE;"))
        await session.commit()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async test client with database dependency override."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a verified test user."""
    user = User(
        email="student@latium.ai",
        hashed_password=get_password_hash("SecretPassword123!"),
        full_name="Marcus Tullius",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_superuser(db_session: AsyncSession) -> User:
    """Create a test superuser."""
    admin = User(
        email="magister@latium.ai",
        hashed_password=get_password_hash("AdminPassword123!"),
        full_name="Seneca Magister",
        is_active=True,
        is_superuser=True,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin

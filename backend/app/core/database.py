import os
import sys
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings

_engine_kwargs: dict[str, Any] = {
    "echo": settings.DEBUG,
    "future": True,
    "pool_pre_ping": True,
}
if (
    "pytest" in sys.modules
    or os.environ.get("PYTEST_CURRENT_TEST")
    or settings.ENVIRONMENT == "test"
):
    _engine_kwargs["poolclass"] = NullPool

engine = create_async_engine(
    settings.async_database_url,
    **_engine_kwargs,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async SQLAlchemy session with rollback on exception."""
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

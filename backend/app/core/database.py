"""
database.py — Async SQLAlchemy engine and session factory.

Security rule (enforced here, apply everywhere):
  DATABASE_URL contains a password — NEVER log the full URL.
  Only log host and database name extracted from the URL.
"""
import logging
import re
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

logger = logging.getLogger("app.core.database")


def _redact_db_url(url: str) -> str:
    """
    Return host + database name from a DATABASE_URL, stripping credentials.

    postgresql://user:password@host:port/dbname  →  host:port/dbname
    """
    # Match anything after '@' up to end of string
    match = re.search(r"@(.+)$", url)
    if match:
        return match.group(1)
    # Fallback: return only the scheme if the URL is malformed
    return url.split("://")[0] if "://" in url else "<unknown>"


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
# Alembic uses the synchronous DATABASE_URL (postgresql://...).
# SQLAlchemy async engine requires the asyncpg driver (postgresql+asyncpg://...).
_async_url = settings.DATABASE_URL.replace(
    "postgresql://", "postgresql+asyncpg://", 1
).replace(
    "postgresql+psycopg2://", "postgresql+asyncpg://", 1
)

engine = create_async_engine(
    _async_url,
    echo=False,          # Never echo SQL — would leak query values in logs
    pool_pre_ping=True,  # Detect stale connections before use
    pool_size=10,
    max_overflow=20,
)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,   # Don't expire objects after commit (avoids lazy-load errors in async)
    autoflush=False,
    autocommit=False,
)


async def log_db_connection() -> None:
    """
    Test connectivity at startup and log redacted host info.
    Called from main.py lifespan — not re-exported as a dependency.
    """
    from sqlalchemy import text
    redacted = _redact_db_url(settings.DATABASE_URL)
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        logger.info("Database connection established", extra={"db_target": redacted})
    except Exception as e:
        logger.warning(
            "Database connectivity test failed. The database might not be reachable. "
            "Target: %s. Error: %s", redacted, e
        )


# ---------------------------------------------------------------------------
# Session dependency (used by FastAPI route handlers via Depends)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def _session_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Internal context manager that guarantees rollback + close on any error.
    Prevents connection leaks that would surface confusingly in later phases.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a managed AsyncSession.
    Usage in route: db: AsyncSession = Depends(get_db)
    """
    async with _session_context() as session:
        yield session

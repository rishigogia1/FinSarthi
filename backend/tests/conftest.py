"""
tests/conftest.py — Pytest fixtures for FinSarthi auth testing.

Defines database and client fixtures. Skips tests gracefully if Postgres
or Redis are not running.
"""
import asyncio
import os
import pytest
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import create_engine, text
from alembic.config import Config
from alembic import command as alembic_command
from fastapi.testclient import TestClient

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Load test environment variables before importing app or settings
os.environ["ENVIRONMENT"] = "test"
test_env_file = os.path.join(BACKEND_DIR, ".env.test")
if os.path.exists(test_env_file):
    with open(test_env_file, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if line_str and not line_str.startswith("#") and "=" in line_str:
                k, v = line_str.split("=", 1)
                os.environ[k] = v

from app.main import app
from app.core.config import settings
from app.core.dependencies import get_db

def _load_test_db_url() -> str:
    """Load test DATABASE_URL from .env.test or fallback to settings with _test suffix."""
    test_env_file = os.path.join(BACKEND_DIR, ".env.test")
    if os.path.exists(test_env_file):
        with open(test_env_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("DATABASE_URL="):
                    return line.strip().split("=", 1)[1]
    url = settings.DATABASE_URL
    if not url.endswith("_test"):
        url = url.rsplit("/", 1)[0] + "/finsarthi_test"
    return url

def _can_connect_db(url: str) -> bool:
    """Check if PostgreSQL is running."""
    sync_url = url.replace("postgresql+asyncpg://", "postgresql://")
    sync_url = sync_url.replace("postgresql+psycopg2://", "postgresql://")
    try:
        engine = create_engine(sync_url, connect_args={"connect_timeout": 2})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return True
    except Exception:
        return False

def _run_migrations(db_url: str, upgrade: bool = True) -> None:
    """Run Alembic migrations up or down on the test database."""
    sync_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    sync_url = sync_url.replace("postgresql+psycopg2://", "postgresql://")
    
    cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    cfg.set_main_option("sqlalchemy.url", sync_url.replace("%", "%%"))
    
    if upgrade:
        alembic_command.upgrade(cfg, "head")
    else:
        try:
            alembic_command.downgrade(cfg, "base")
        except Exception:
            pass

# Scope to session so migrations run once per test run
@pytest.fixture(scope="session")
def setup_test_db():
    db_url = _load_test_db_url()
    if not _can_connect_db(db_url):
        pytest.skip("Postgres is not running or unreachable — skipping DB integration tests")
    
    # Run migrations up
    _run_migrations(db_url, upgrade=True)
    yield db_url

@pytest.fixture
async def db_session(setup_test_db) -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session wrapped in a transaction that rolls back."""
    db_url = setup_test_db
    # Force asyncpg driver for AsyncSession usage
    if not db_url.startswith("postgresql+asyncpg://"):
        async_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
    else:
        async_url = db_url

    engine = create_async_engine(async_url, echo=False)
    
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE users, refresh_tokens RESTART IDENTITY CASCADE;"))
    
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with engine.begin() as conn:
        async with AsyncSession(conn, expire_on_commit=False) as session:
            yield session
            await session.rollback()
    
    await engine.dispose()

@pytest.fixture
def client(setup_test_db) -> Generator[TestClient, None, None]:
    """Provide a TestClient connected to the test database."""
    with TestClient(app) as test_client:
        yield test_client

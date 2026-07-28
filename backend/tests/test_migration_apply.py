"""
test_migration_apply.py — Verify the Alembic migration applies and reverses cleanly.

Runs against the test database (DATABASE_URL from .env.test).
Requires a live PostgreSQL instance.

Test strategy:
  1. Run `alembic upgrade head` → all 11 tables must exist.
  2. Run `alembic downgrade base` → all 11 tables must be gone.
This proves the migration is fully reversible, which CI uses to reset the test DB.
"""
import os
import pytest
from sqlalchemy import create_engine, inspect, text
from alembic.config import Config
from alembic import command as alembic_command


# ---------------------------------------------------------------------------
# Resolve test DATABASE_URL from .env.test
# ---------------------------------------------------------------------------
def _load_test_db_url() -> str:
    env_test_path = os.path.join(os.path.dirname(__file__), "..", ".env.test")
    env_test_path = os.path.abspath(env_test_path)
    url = None
    if os.path.exists(env_test_path):
        with open(env_test_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("DATABASE_URL="):
                    url = line.split("=", 1)[1].strip()
                    break
    if not url:
        pytest.skip("DATABASE_URL not found in .env.test — skipping migration tests")
    # Normalize to sync psycopg2 driver for Alembic CLI usage
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    url = url.replace("postgresql+psycopg2://", "postgresql://")
    return url


TEST_DB_URL = None

ALL_TABLES = [
    "users",
    "refresh_tokens",
    "digital_twins",
    "user_preferences",
    "conversations",
    "messages",
    "agent_runs",
    "agent_logs",
    "goals",
    "knowledge_sources",
    "audit_logs",
]

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _alembic_cfg(db_url: str) -> Config:
    """Return an Alembic Config pointed at alembic.ini with URL overridden."""
    cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


def _run_upgrade(db_url: str) -> None:
    alembic_command.upgrade(_alembic_cfg(db_url), "head")


def _run_downgrade(db_url: str) -> None:
    alembic_command.downgrade(_alembic_cfg(db_url), "base")


def _can_connect(url: str) -> bool:
    """Return True if we can connect to the given DB URL."""
    try:
        engine = create_engine(url, connect_args={"connect_timeout": 3})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return True
    except Exception:
        return False


@pytest.fixture(scope="module", autouse=True)
def db_url():
    global TEST_DB_URL
    TEST_DB_URL = _load_test_db_url()
    if not _can_connect(TEST_DB_URL):
        pytest.skip(f"Cannot connect to test DB at {TEST_DB_URL} — is Postgres running?")
    yield TEST_DB_URL


@pytest.fixture(autouse=True)
def ensure_clean_state():
    """
    Bring DB to a clean baseline before each test:
    downgrade to base first (idempotent if already at base).
    """
    try:
        _run_downgrade(TEST_DB_URL)
    except Exception:
        pass  # Already at base — ignore errors
    yield
    # Cleanup after each test too
    try:
        _run_downgrade(TEST_DB_URL)
    except Exception:
        pass


class TestMigrationApply:
    def test_upgrade_head_succeeds(self):
        _run_upgrade(TEST_DB_URL)  # Raises on failure

    def test_all_tables_exist_after_upgrade(self):
        _run_upgrade(TEST_DB_URL)
        engine = create_engine(TEST_DB_URL)
        inspector = inspect(engine)
        existing = set(inspector.get_table_names())
        engine.dispose()
        for table in ALL_TABLES:
            assert table in existing, f"Table '{table}' missing after upgrade head"

    def test_downgrade_base_succeeds(self):
        _run_upgrade(TEST_DB_URL)
        _run_downgrade(TEST_DB_URL)  # Raises on failure

    def test_all_tables_gone_after_downgrade(self):
        _run_upgrade(TEST_DB_URL)
        _run_downgrade(TEST_DB_URL)
        engine = create_engine(TEST_DB_URL)
        inspector = inspect(engine)
        existing = set(inspector.get_table_names())
        engine.dispose()
        for table in ALL_TABLES:
            assert table not in existing, f"Table '{table}' still exists after downgrade base"

    def test_upgrade_is_idempotent(self):
        """Running upgrade head twice should not error."""
        _run_upgrade(TEST_DB_URL)
        _run_upgrade(TEST_DB_URL)  # second run is a no-op, should not raise

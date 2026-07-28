"""
alembic/env.py — Alembic migration environment.

Key responsibilities:
  1. Load DATABASE_URL from Settings (never hardcoded).
  2. Import all models via app.models so Base.metadata is fully populated
     before autogenerate or migration runs.
  3. Strip the asyncpg driver prefix when running synchronous migrations
     (Alembic CLI uses psycopg2; the async engine uses asyncpg).
"""
import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# ---------------------------------------------------------------------------
# Ensure the backend/ directory is on sys.path so app.* imports work
# whether alembic is run from backend/ or from the repo root.
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---------------------------------------------------------------------------
# Import Settings to resolve DATABASE_URL at runtime (never hardcode here)
# ---------------------------------------------------------------------------
from app.core.config import settings  # noqa: E402

# ---------------------------------------------------------------------------
# Import ALL models so Base.metadata contains the full schema.
# If a model is missing here, autogenerate will silently omit that table.
# ---------------------------------------------------------------------------
from app.models import Base  # noqa: E402 — this triggers all model imports via __init__.py

# Alembic config object (reads alembic.ini)
config = context.config

# Wire up Python logging from alembic.ini's [loggers] section
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata for autogenerate support
target_metadata = Base.metadata

# ---------------------------------------------------------------------------
# Override the URL from alembic.ini with the real value from Settings.
# Alembic CLI runs synchronously, so replace asyncpg with psycopg2.
# ---------------------------------------------------------------------------
def _sync_url() -> str:
    url = settings.DATABASE_URL
    # Normalize asyncpg driver references to psycopg2 for sync Alembic CLI usage
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    url = url.replace("postgresql+psycopg2://", "postgresql://")
    return url


def run_migrations_offline() -> None:
    """
    Run migrations without a live DB connection (outputs SQL to stdout).
    Used by: alembic upgrade head --sql
    """
    url = _sync_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations with a live DB connection.
    Used by: alembic upgrade head (normal usage)
    """
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = _sync_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

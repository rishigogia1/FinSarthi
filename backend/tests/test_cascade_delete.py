"""
test_cascade_delete.py — Verify the full cascade chain from users down.

This is the most critical test in Phase 4. It proves that deleting a user
wipes every dependent row, including rows 3+ levels deep in the chain.

Full dependency tree tested:
  users
  ├── refresh_tokens          (direct FK → users)
  ├── digital_twins           (direct FK → users)
  ├── user_preferences        (direct FK → users)
  ├── goals                   (direct FK → users)
  ├── audit_logs              (direct FK → users)
  └── conversations           (direct FK → users)
      └── messages            (FK → conversations)
          ── agent_runs       (FK → conversations, same parent as messages)
              └── agent_logs  (FK → agent_runs)

After deleting the user, all 9 dependent rows must be gone.

Requires: live PostgreSQL at DATABASE_URL in .env.test + migration already applied.
"""
import os
import pytest
from datetime import datetime, timezone

from sqlalchemy import create_engine, text
from alembic.config import Config
from alembic import command as alembic_command

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _load_test_db_url() -> str:
    env_test_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", ".env.test")
    )
    url = None
    if os.path.exists(env_test_path):
        with open(env_test_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("DATABASE_URL="):
                    url = line.split("=", 1)[1].strip()
                    break
    if not url:
        pytest.skip("DATABASE_URL not found in .env.test")
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    url = url.replace("postgresql+psycopg2://", "postgresql://")
    return url


def _alembic_cfg(db_url: str) -> Config:
    cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


def _run_upgrade(db_url: str) -> None:
    alembic_command.upgrade(_alembic_cfg(db_url), "head")


def _run_downgrade(db_url: str) -> None:
    alembic_command.downgrade(_alembic_cfg(db_url), "base")


def _can_connect(url: str) -> bool:
    try:
        engine = create_engine(url, connect_args={"connect_timeout": 3})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def db_engine():
    url = _load_test_db_url()
    if not _can_connect(url):
        pytest.skip(f"Cannot connect to test DB — is Postgres running?")

    # Ensure schema is applied
    _run_upgrade(url)

    engine = create_engine(url)
    yield engine
    engine.dispose()

    # Clean up after the whole module — leave DB at clean state for next run
    try:
        _run_downgrade(url)
    except Exception:
        pass


@pytest.fixture
def conn(db_engine):
    """Provide a connection with automatic rollback after each test."""
    with db_engine.connect() as connection:
        with connection.begin():
            yield connection
            connection.rollback()


# ---------------------------------------------------------------------------
# The cascade test
# ---------------------------------------------------------------------------
class TestCascadeDelete:
    """
    Insert one row in every table of the cascade tree, then delete the user,
    and assert every dependent row — including the deeply nested agent_log —
    is gone.
    """

    def test_full_cascade_chain(self, conn):
        now = datetime.now(timezone.utc).isoformat()

        # --- users ---
        conn.execute(text("""
            INSERT INTO users (id, name, email, password_hash, created_at, updated_at)
            VALUES (
                gen_random_uuid(),
                'Cascade Test User',
                'cascade_test@example.com',
                'hashed_pw',
                now(), now()
            )
        """))
        user_id = conn.execute(
            text("SELECT id FROM users WHERE email = 'cascade_test@example.com'")
        ).scalar()
        assert user_id is not None, "User row was not created"

        # --- refresh_tokens (direct FK → users) ---
        conn.execute(text(f"""
            INSERT INTO refresh_tokens (id, user_id, token_hash, expires_at, revoked)
            VALUES (gen_random_uuid(), '{user_id}', 'testhash123', now() + interval '7 days', false)
        """))

        # --- digital_twins (direct FK → users) ---
        conn.execute(text(f"""
            INSERT INTO digital_twins (id, user_id, accessibility_needs, updated_at)
            VALUES (gen_random_uuid(), '{user_id}', '{{}}'::jsonb, now())
        """))

        # --- user_preferences (direct FK → users) ---
        conn.execute(text(f"""
            INSERT INTO user_preferences (id, user_id, theme, notifications_enabled, updated_at)
            VALUES (gen_random_uuid(), '{user_id}', 'light', true, now())
        """))

        # --- goals (direct FK → users) ---
        conn.execute(text(f"""
            INSERT INTO goals (id, user_id, goal_name, target_amount, current_amount, status)
            VALUES (gen_random_uuid(), '{user_id}', 'Emergency Fund', 50000.00, 0.00, 'active')
        """))

        # --- audit_logs (direct FK → users) ---
        conn.execute(text(f"""
            INSERT INTO audit_logs (id, user_id, action, created_at)
            VALUES (gen_random_uuid(), '{user_id}', 'account_created', now())
        """))

        # --- conversations (direct FK → users) ---
        conn.execute(text(f"""
            INSERT INTO conversations (id, user_id, title, created_at)
            VALUES (gen_random_uuid(), '{user_id}', 'Test Chat', now())
        """))
        conv_id = conn.execute(
            text(f"SELECT id FROM conversations WHERE user_id = '{user_id}'")
        ).scalar()
        assert conv_id is not None

        # --- messages (FK → conversations) ---
        conn.execute(text(f"""
            INSERT INTO messages (id, conversation_id, role, content, created_at)
            VALUES (gen_random_uuid(), '{conv_id}', 'user', 'Hello', now())
        """))

        # --- agent_runs (FK → conversations) ---
        conn.execute(text(f"""
            INSERT INTO agent_runs (id, conversation_id, agent_name, status, started_at)
            VALUES (gen_random_uuid(), '{conv_id}', 'guardian', 'completed', now())
        """))
        run_id = conn.execute(
            text(f"SELECT id FROM agent_runs WHERE conversation_id = '{conv_id}'")
        ).scalar()
        assert run_id is not None

        # --- agent_logs (FK → agent_runs — deepest node) ---
        conn.execute(text(f"""
            INSERT INTO agent_logs (id, agent_run_id, event_type, created_at)
            VALUES (gen_random_uuid(), '{run_id}', 'output', now())
        """))

        # --- transactions ---
        conn.execute(text(f"""
            INSERT INTO transactions (id, user_id, type, amount, category, occurred_on)
            VALUES (gen_random_uuid(), '{user_id}', 'expense', 100.00, 'Food', now())
        """))

        # --- recurring_cashflows ---
        conn.execute(text(f"""
            INSERT INTO recurring_cashflows (id, user_id, type, amount, category, start_date)
            VALUES (gen_random_uuid(), '{user_id}', 'expense', 1200.00, 'Rent', now())
        """))

        # --- budgets ---
        conn.execute(text(f"""
            INSERT INTO budgets (id, user_id, category, limit_amount, start_date)
            VALUES (gen_random_uuid(), '{user_id}', 'Food', 500.00, now())
        """))

        # --- import_jobs ---
        conn.execute(text(f"""
            INSERT INTO import_jobs (id, user_id, filename, status, total_rows)
            VALUES (gen_random_uuid(), '{user_id}', 'test.csv', 'uploaded', 10)
        """))

        # --- notifications ---
        conn.execute(text(f"""
            INSERT INTO notifications (id, user_id, title, message, type)
            VALUES (gen_random_uuid(), '{user_id}', 'Budget warning', 'Nearing budget limit', 'budget_limit')
        """))

        # Verify all rows exist before deletion
        counts = {
            "refresh_tokens": conn.execute(text(f"SELECT COUNT(*) FROM refresh_tokens WHERE user_id = '{user_id}'")).scalar(),
            "digital_twins": conn.execute(text(f"SELECT COUNT(*) FROM digital_twins WHERE user_id = '{user_id}'")).scalar(),
            "user_preferences": conn.execute(text(f"SELECT COUNT(*) FROM user_preferences WHERE user_id = '{user_id}'")).scalar(),
            "goals": conn.execute(text(f"SELECT COUNT(*) FROM goals WHERE user_id = '{user_id}'")).scalar(),
            "audit_logs": conn.execute(text(f"SELECT COUNT(*) FROM audit_logs WHERE user_id = '{user_id}'")).scalar(),
            "conversations": conn.execute(text(f"SELECT COUNT(*) FROM conversations WHERE user_id = '{user_id}'")).scalar(),
            "messages": conn.execute(text(f"SELECT COUNT(*) FROM messages WHERE conversation_id = '{conv_id}'")).scalar(),
            "agent_runs": conn.execute(text(f"SELECT COUNT(*) FROM agent_runs WHERE conversation_id = '{conv_id}'")).scalar(),
            "agent_logs": conn.execute(text(f"SELECT COUNT(*) FROM agent_logs WHERE agent_run_id = '{run_id}'")).scalar(),
            "transactions": conn.execute(text(f"SELECT COUNT(*) FROM transactions WHERE user_id = '{user_id}'")).scalar(),
            "recurring_cashflows": conn.execute(text(f"SELECT COUNT(*) FROM recurring_cashflows WHERE user_id = '{user_id}'")).scalar(),
            "budgets": conn.execute(text(f"SELECT COUNT(*) FROM budgets WHERE user_id = '{user_id}'")).scalar(),
            "import_jobs": conn.execute(text(f"SELECT COUNT(*) FROM import_jobs WHERE user_id = '{user_id}'")).scalar(),
            "notifications": conn.execute(text(f"SELECT COUNT(*) FROM notifications WHERE user_id = '{user_id}'")).scalar(),
        }
        for table, count in counts.items():
            assert count == 1, f"Expected 1 row in {table} before delete, got {count}"

        # ---------------------------------------------------------------
        # THE CRITICAL ASSERTION: delete the user → everything must cascade
        # ---------------------------------------------------------------
        conn.execute(text(f"DELETE FROM users WHERE id = '{user_id}'"))

        # Assert all dependent rows are gone
        assert conn.execute(text(f"SELECT COUNT(*) FROM refresh_tokens WHERE user_id = '{user_id}'")).scalar() == 0, \
            "refresh_tokens cascade failed"
        assert conn.execute(text(f"SELECT COUNT(*) FROM digital_twins WHERE user_id = '{user_id}'")).scalar() == 0, \
            "digital_twins cascade failed"
        assert conn.execute(text(f"SELECT COUNT(*) FROM user_preferences WHERE user_id = '{user_id}'")).scalar() == 0, \
            "user_preferences cascade failed"
        assert conn.execute(text(f"SELECT COUNT(*) FROM goals WHERE user_id = '{user_id}'")).scalar() == 0, \
            "goals cascade failed"
        assert conn.execute(text(f"SELECT COUNT(*) FROM audit_logs WHERE user_id = '{user_id}'")).scalar() == 0, \
            "audit_logs cascade failed"
        assert conn.execute(text(f"SELECT COUNT(*) FROM conversations WHERE user_id = '{user_id}'")).scalar() == 0, \
            "conversations cascade failed"
        assert conn.execute(text(f"SELECT COUNT(*) FROM messages WHERE conversation_id = '{conv_id}'")).scalar() == 0, \
            "messages cascade failed (conversation → messages chain broken)"
        assert conn.execute(text(f"SELECT COUNT(*) FROM agent_runs WHERE conversation_id = '{conv_id}'")).scalar() == 0, \
            "agent_runs cascade failed (conversation → agent_runs chain broken)"
        assert conn.execute(text(f"SELECT COUNT(*) FROM agent_logs WHERE agent_run_id = '{run_id}'")).scalar() == 0, \
            "agent_logs cascade failed (agent_run → agent_logs chain broken — deepest node)"
        assert conn.execute(text(f"SELECT COUNT(*) FROM transactions WHERE user_id = '{user_id}'")).scalar() == 0, \
            "transactions cascade failed"
        assert conn.execute(text(f"SELECT COUNT(*) FROM recurring_cashflows WHERE user_id = '{user_id}'")).scalar() == 0, \
            "recurring_cashflows cascade failed"
        assert conn.execute(text(f"SELECT COUNT(*) FROM budgets WHERE user_id = '{user_id}'")).scalar() == 0, \
            "budgets cascade failed"
        assert conn.execute(text(f"SELECT COUNT(*) FROM import_jobs WHERE user_id = '{user_id}'")).scalar() == 0, \
            "import_jobs cascade failed"
        assert conn.execute(text(f"SELECT COUNT(*) FROM notifications WHERE user_id = '{user_id}'")).scalar() == 0, \
            "notifications cascade failed"

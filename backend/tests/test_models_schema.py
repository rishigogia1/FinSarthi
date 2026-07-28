"""
test_models_schema.py — Verify SQLAlchemy model structure matches Phase 3's spec.

These tests inspect the ORM metadata directly — no database connection required.
They catch column renames, missing fields, wrong nullability, and FK target errors
before any migration is run.
"""
import pytest
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import class_mapper

# Import all models (this also registers them against Base.metadata)
from app.models import (
    Base,
    User,
    RefreshToken,
    DigitalTwin,
    UserPreference,
    Conversation,
    Message,
    AgentRun,
    AgentLog,
    Goal,
    KnowledgeSource,
    AuditLog,
    Transaction,
    RecurringCashflow,
    Budget,
    ImportJob,
    Notification,
)


def _col(model, col_name):
    """Return the SQLAlchemy Column for a given model and column name."""
    mapper = class_mapper(model)
    for col in mapper.columns:
        if col.key == col_name:
            return col
    raise AssertionError(f"Column '{col_name}' not found on {model.__tablename__}")


def _fk_targets(model, col_name):
    """Return the set of FK target table.column strings for a column."""
    col = _col(model, col_name)
    return {fk.target_fullname for fk in col.foreign_keys}


# ---------------------------------------------------------------------------
# users
# ---------------------------------------------------------------------------
class TestUserModel:
    def test_table_name(self):
        assert User.__tablename__ == "users"

    def test_required_columns_exist(self):
        for col_name in ("id", "name", "email", "password_hash", "role", "last_login_at", "onboarding_completed", "created_at", "updated_at"):
            _col(User, col_name)  # raises AssertionError if missing

    def test_email_is_not_nullable(self):
        assert not _col(User, "email").nullable

    def test_name_is_not_nullable(self):
        assert not _col(User, "name").nullable

    def test_password_hash_is_not_nullable(self):
        assert not _col(User, "password_hash").nullable

    def test_email_has_unique_constraint(self):
        col = _col(User, "email")
        assert col.unique or any(
            "email" in [c.name for c in uc.columns]
            for uc in User.__table__.constraints
            if hasattr(uc, "columns")
        )


# ---------------------------------------------------------------------------
# refresh_tokens
# ---------------------------------------------------------------------------
class TestRefreshTokenModel:
    def test_table_name(self):
        assert RefreshToken.__tablename__ == "refresh_tokens"

    def test_required_columns_exist(self):
        for col_name in ("id", "user_id", "token_hash", "expires_at", "revoked"):
            _col(RefreshToken, col_name)

    def test_user_id_not_nullable(self):
        assert not _col(RefreshToken, "user_id").nullable

    def test_user_id_fk_points_to_users(self):
        assert "users.id" in _fk_targets(RefreshToken, "user_id")

    def test_revoked_not_nullable(self):
        assert not _col(RefreshToken, "revoked").nullable

    def test_token_hash_not_nullable(self):
        assert not _col(RefreshToken, "token_hash").nullable


# ---------------------------------------------------------------------------
# digital_twins
# ---------------------------------------------------------------------------
class TestDigitalTwinModel:
    def test_table_name(self):
        assert DigitalTwin.__tablename__ == "digital_twins"

    def test_required_columns_exist(self):
        for col_name in ("id", "user_id", "accessibility_needs", "updated_at"):
            _col(DigitalTwin, col_name)

    def test_nullable_columns(self):
        for col_name in ("financial_goals", "income_pattern", "risk_appetite",
                         "literacy_level", "language_preference", "behavioral_notes"):
            assert _col(DigitalTwin, col_name).nullable, f"{col_name} should be nullable"

    def test_accessibility_needs_not_nullable(self):
        assert not _col(DigitalTwin, "accessibility_needs").nullable

    def test_user_id_fk_points_to_users(self):
        assert "users.id" in _fk_targets(DigitalTwin, "user_id")

    def test_user_id_unique(self):
        col = _col(DigitalTwin, "user_id")
        assert col.unique or any(
            "user_id" in [c.name for c in uc.columns]
            for uc in DigitalTwin.__table__.constraints
            if hasattr(uc, "columns")
        )


# ---------------------------------------------------------------------------
# user_preferences
# ---------------------------------------------------------------------------
class TestUserPreferenceModel:
    def test_table_name(self):
        assert UserPreference.__tablename__ == "user_preferences"

    def test_required_columns_exist(self):
        for col_name in ("id", "user_id", "theme", "notifications_enabled", "updated_at"):
            _col(UserPreference, col_name)

    def test_user_id_fk_points_to_users(self):
        assert "users.id" in _fk_targets(UserPreference, "user_id")

    def test_theme_not_nullable(self):
        assert not _col(UserPreference, "theme").nullable

    def test_notifications_not_nullable(self):
        assert not _col(UserPreference, "notifications_enabled").nullable


# ---------------------------------------------------------------------------
# conversations
# ---------------------------------------------------------------------------
class TestConversationModel:
    def test_table_name(self):
        assert Conversation.__tablename__ == "conversations"

    def test_required_columns_exist(self):
        for col_name in ("id", "user_id", "title", "created_at"):
            _col(Conversation, col_name)

    def test_title_is_nullable(self):
        assert _col(Conversation, "title").nullable

    def test_user_id_fk_points_to_users(self):
        assert "users.id" in _fk_targets(Conversation, "user_id")


# ---------------------------------------------------------------------------
# messages
# ---------------------------------------------------------------------------
class TestMessageModel:
    def test_table_name(self):
        assert Message.__tablename__ == "messages"

    def test_required_columns_exist(self):
        for col_name in ("id", "conversation_id", "role", "content", "created_at"):
            _col(Message, col_name)

    def test_role_not_nullable(self):
        assert not _col(Message, "role").nullable

    def test_content_not_nullable(self):
        assert not _col(Message, "content").nullable

    def test_conversation_id_fk_points_to_conversations(self):
        assert "conversations.id" in _fk_targets(Message, "conversation_id")


# ---------------------------------------------------------------------------
# agent_runs
# ---------------------------------------------------------------------------
class TestAgentRunModel:
    def test_table_name(self):
        assert AgentRun.__tablename__ == "agent_runs"

    def test_required_columns_exist(self):
        for col_name in ("id", "conversation_id", "agent_name", "status", "started_at", "completed_at"):
            _col(AgentRun, col_name)

    def test_completed_at_is_nullable(self):
        assert _col(AgentRun, "completed_at").nullable

    def test_conversation_id_fk_points_to_conversations(self):
        assert "conversations.id" in _fk_targets(AgentRun, "conversation_id")


# ---------------------------------------------------------------------------
# agent_logs
# ---------------------------------------------------------------------------
class TestAgentLogModel:
    def test_table_name(self):
        assert AgentLog.__tablename__ == "agent_logs"

    def test_required_columns_exist(self):
        for col_name in ("id", "agent_run_id", "event_type", "detail", "created_at"):
            _col(AgentLog, col_name)

    def test_detail_is_nullable(self):
        assert _col(AgentLog, "detail").nullable

    def test_agent_run_id_fk_points_to_agent_runs(self):
        assert "agent_runs.id" in _fk_targets(AgentLog, "agent_run_id")


# ---------------------------------------------------------------------------
# goals
# ---------------------------------------------------------------------------
class TestGoalModel:
    def test_table_name(self):
        assert Goal.__tablename__ == "goals"

    def test_required_columns_exist(self):
        for col_name in ("id", "user_id", "goal_name", "target_amount", "current_amount", "status"):
            _col(Goal, col_name)

    def test_deadline_is_nullable(self):
        assert _col(Goal, "deadline").nullable

    def test_user_id_fk_points_to_users(self):
        assert "users.id" in _fk_targets(Goal, "user_id")


# ---------------------------------------------------------------------------
# knowledge_sources
# ---------------------------------------------------------------------------
class TestKnowledgeSourceModel:
    def test_table_name(self):
        assert KnowledgeSource.__tablename__ == "knowledge_sources"

    def test_required_columns_exist(self):
        for col_name in ("id", "source_name", "ingested_at", "active"):
            _col(KnowledgeSource, col_name)

    def test_category_is_nullable(self):
        assert _col(KnowledgeSource, "category").nullable

    def test_no_user_fk(self):
        """knowledge_sources is a global table — must have no FK to users."""
        fks = KnowledgeSource.__table__.foreign_keys
        user_fks = [fk for fk in fks if "users" in fk.target_fullname]
        assert not user_fks, "knowledge_sources must not have a FK to users"


# ---------------------------------------------------------------------------
# audit_logs
# ---------------------------------------------------------------------------
class TestAuditLogModel:
    def test_table_name(self):
        assert AuditLog.__tablename__ == "audit_logs"

    def test_required_columns_exist(self):
        for col_name in ("id", "user_id", "action", "before", "after", "created_at"):
            _col(AuditLog, col_name)

    def test_before_and_after_are_nullable(self):
        assert _col(AuditLog, "before").nullable
        assert _col(AuditLog, "after").nullable

    def test_action_not_nullable(self):
        assert not _col(AuditLog, "action").nullable

    def test_user_id_fk_points_to_users(self):
        assert "users.id" in _fk_targets(AuditLog, "user_id")


# ---------------------------------------------------------------------------
# transactions
# ---------------------------------------------------------------------------
class TestTransactionModel:
    def test_table_name(self):
        assert Transaction.__tablename__ == "transactions"

    def test_required_columns_exist(self):
        for col_name in ("id", "user_id", "type", "amount", "currency", "category",
                         "occurred_on", "note", "source", "created_at", "updated_at"):
            _col(Transaction, col_name)

    def test_user_id_fk_points_to_users(self):
        assert "users.id" in _fk_targets(Transaction, "user_id")

    def test_type_not_nullable(self):
        assert not _col(Transaction, "type").nullable

    def test_amount_not_nullable(self):
        assert not _col(Transaction, "amount").nullable


# ---------------------------------------------------------------------------
# recurring_cashflows
# ---------------------------------------------------------------------------
class TestRecurringCashflowModel:
    def test_table_name(self):
        assert RecurringCashflow.__tablename__ == "recurring_cashflows"

    def test_required_columns_exist(self):
        for col_name in ("id", "user_id", "type", "amount", "category", "frequency",
                         "start_date", "end_date", "active", "note", "created_at", "updated_at"):
            _col(RecurringCashflow, col_name)

    def test_user_id_fk_points_to_users(self):
        assert "users.id" in _fk_targets(RecurringCashflow, "user_id")

    def test_type_not_nullable(self):
        assert not _col(RecurringCashflow, "type").nullable

    def test_amount_not_nullable(self):
        assert not _col(RecurringCashflow, "amount").nullable


# ---------------------------------------------------------------------------
# budgets
# ---------------------------------------------------------------------------
class TestBudgetModel:
    def test_table_name(self):
        assert Budget.__tablename__ == "budgets"

    def test_required_columns_exist(self):
        for col_name in ("id", "user_id", "category", "limit_amount", "period",
                         "start_date", "end_date", "active", "created_at", "updated_at"):
            _col(Budget, col_name)

    def test_user_id_fk_points_to_users(self):
        assert "users.id" in _fk_targets(Budget, "user_id")

    def test_category_not_nullable(self):
        assert not _col(Budget, "category").nullable

    def test_limit_amount_not_nullable(self):
        assert not _col(Budget, "limit_amount").nullable


# ---------------------------------------------------------------------------
# import_jobs
# ---------------------------------------------------------------------------
class TestImportJobModel:
    def test_table_name(self):
        assert ImportJob.__tablename__ == "import_jobs"

    def test_required_columns_exist(self):
        for col_name in ("id", "user_id", "filename", "status", "total_rows",
                         "accepted_rows", "duplicate_rows", "rejected_rows",
                         "error_summary", "raw_data", "created_at", "updated_at"):
            _col(ImportJob, col_name)

    def test_user_id_fk_points_to_users(self):
        assert "users.id" in _fk_targets(ImportJob, "user_id")


# ---------------------------------------------------------------------------
# notifications
# ---------------------------------------------------------------------------
class TestNotificationModel:
    def test_table_name(self):
        assert Notification.__tablename__ == "notifications"

    def test_required_columns_exist(self):
        for col_name in ("id", "user_id", "title", "message", "type", "read",
                         "archived", "delivery_channel", "delivered_at", "created_at"):
            _col(Notification, col_name)

    def test_user_id_fk_points_to_users(self):
        assert "users.id" in _fk_targets(Notification, "user_id")

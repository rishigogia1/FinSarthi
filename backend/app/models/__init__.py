"""
models/__init__.py — Import all models so a single import exposes everything.

Alembic's env.py imports from here to ensure all models are registered
against Base.metadata before autogenerate inspects the schema.
"""
from app.models.base import Base
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.models.digital_twin import DigitalTwin
from app.models.user_preference import UserPreference
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.agent_run import AgentRun
from app.models.agent_log import AgentLog
from app.models.goal import Goal
from app.models.knowledge_source import KnowledgeSource
from app.models.audit_log import AuditLog
from app.models.transaction import Transaction
from app.models.recurring_cashflow import RecurringCashflow
from app.models.budget import Budget
from app.models.import_job import ImportJob
from app.models.notification import Notification

__all__ = [
    "Base",
    "User",
    "RefreshToken",
    "DigitalTwin",
    "UserPreference",
    "Conversation",
    "Message",
    "AgentRun",
    "AgentLog",
    "Goal",
    "KnowledgeSource",
    "AuditLog",
    "Transaction",
    "RecurringCashflow",
    "Budget",
    "ImportJob",
    "Notification",
]

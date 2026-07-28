"""
schemas/admin.py — Data validation schemas for administration context queries.
"""
from datetime import datetime
from typing import Any
from pydantic import BaseModel


class AdminUserSummary(BaseModel):
    user_id: str
    name: str
    email: str
    role: str
    last_login_at: datetime | None
    onboarding_completed: bool
    transaction_count: int
    budget_count: int
    goal_count: int

    class Config:
        from_attributes = True


class AdminUserListResponse(BaseModel):
    users: list[AdminUserSummary]


class SystemAuditLogEntry(BaseModel):
    id: str
    user_id: str
    action: str
    before: dict[str, Any] | None
    after: dict[str, Any] | None
    created_at: datetime

    class Config:
        from_attributes = True


class SystemAuditLogResponse(BaseModel):
    logs: list[SystemAuditLogEntry]


class SystemSummaryResponse(BaseModel):
    database_connected: bool
    redis_connected: bool
    total_users: int
    total_transactions: int
    total_budgets: int
    total_goals: int

"""
schemas/insights.py — Structured user-specific alerts and AI-attributable details.
"""
from typing import Literal
from pydantic import BaseModel


class InsightResponse(BaseModel):
    title: str
    message: str
    type: str  # "budget_alert", "spending_anomaly", "goal_warning", "savings_insight", "low_history"
    severity: Literal["info", "warning", "critical"]
    confidence: Literal["low", "medium", "high"]
    evidence: dict | None = None
    action_hint: str | None = None


class InsightListResponse(BaseModel):
    insights: list[InsightResponse]

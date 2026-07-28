"""
schemas/forecasts.py — Data schemas for moving-average and template-driven future cashflow projections.
"""
from typing import Literal
from pydantic import BaseModel


class MonthlyCashflowForecastResponse(BaseModel):
    predicted_income: float
    predicted_expense: float
    predicted_net: float
    confidence: Literal["low", "medium", "high"]
    reason: str


class BudgetRiskForecastResponse(BaseModel):
    category: str
    budget_limit: float
    predicted_spend: float
    overrun_risk: Literal["low", "medium", "high"]
    confidence: Literal["low", "medium", "high"]


class GoalProjectionResponse(BaseModel):
    goal_id: str
    goal_name: str
    projected_completion_date: str | None  # "YYYY-MM-DD" or None if pace is zero/negative
    is_trackable: bool
    confidence: Literal["low", "medium", "high"]
    reason: str

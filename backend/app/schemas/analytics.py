"""
schemas/analytics.py — Data validation schemas for historical trends and category calculations.
"""
from pydantic import BaseModel


class OverviewAnalyticsResponse(BaseModel):
    total_income: float
    total_expenses: float
    net_savings: float
    savings_rate: float


class SpendingTrendPoint(BaseModel):
    category: str
    total_amount: float
    percentage: float


class CategoryTrendResponse(BaseModel):
    trends: list[SpendingTrendPoint]


class BudgetHealthResponse(BaseModel):
    category: str
    limit_amount: float
    actual_spent: float
    usage_percentage: float
    status: str  # "normal", "warning", "exceeded"


class GoalHealthResponse(BaseModel):
    goal_id: str
    goal_name: str
    target_amount: float
    current_amount: float
    completion_percentage: float
    status: str  # "on_track", "at_risk", "off_track"
    reason: str

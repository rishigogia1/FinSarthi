"""
schemas/summaries.py — Read-only validation models for financial calculations and summaries.
"""
from pydantic import BaseModel


class OverviewSummaryResponse(BaseModel):
    total_income: float
    total_expenses: float
    net_cashflow: float


class CategoryBreakdownResponse(BaseModel):
    category: str
    total_amount: float
    percentage: float
    type: str  # "income" or "expense"


class MonthlyCashflowPoint(BaseModel):
    month: str  # Format: "YYYY-MM"
    income: float
    expense: float
    net: float

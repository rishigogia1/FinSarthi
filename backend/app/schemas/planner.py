"""
schemas/planner.py — Validation and response schemas for Planner & Transactions.
"""
from datetime import date as DateType, datetime
from typing import Literal
from pydantic import BaseModel, Field, field_validator
from app.models.transaction import BUILTIN_CATEGORIES, TRANSACTION_SOURCES


class TransactionCreateSchema(BaseModel):
    type: Literal["expense", "income"] = Field(..., description="Transaction type")
    amount: float = Field(..., gt=0, description="Amount must be greater than zero")
    currency: str = Field("INR", description="Currency code")
    category: str = Field(..., min_length=1, description="Expense or income category")
    occurred_on: DateType | None = Field(default_factory=DateType.today, description="Date transaction occurred")
    note: str | None = Field(None, max_length=500, description="Optional description or note")
    source: str = Field("MANUAL", description="Source: CHAT, MANUAL, IMPORT, BANK_SYNC, API")

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        clean = v.strip().title()
        if not clean:
            raise ValueError("Category cannot be empty")
        # Match case-insensitively with builtin categories
        for cat in BUILTIN_CATEGORIES:
            if cat.lower() == clean.lower():
                return cat
        return clean

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str) -> str:
        upper = v.upper()
        if upper in TRANSACTION_SOURCES:
            return upper
        return "MANUAL"


class TransactionResponseSchema(BaseModel):
    id: str
    user_id: str
    type: str
    amount: float
    currency: str
    category: str
    occurred_on: DateType
    note: str | None
    source: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ParsedIntentSchema(BaseModel):
    intent: Literal[
        "add_expense", "add_income", "query_planner", "query_coach_habits",
        "query_coach_overspending", "query_coach", "query_guardian", "query_learn",
        "query_navigator", "general_chat"
    ] = "general_chat"
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    requires_confirmation: bool = False
    amount: float | None = None
    category: str | None = None
    date: DateType | None = None
    description: str | None = None
    clarification_prompt: str | None = None


class PlannerOverviewSchema(BaseModel):
    monthly_expense: float
    monthly_income: float
    net_cashflow: float
    savings_rate: float


class PlannerCategoryAggregateSchema(BaseModel):
    category: str
    total_amount: float
    percentage: float


class PlannerActivitySchema(BaseModel):
    today_count: int
    latest_category: str | None
    last_transaction_amount: float | None
    last_transaction_type: str | None


class PlannerAnalyticsMetricsSchema(BaseModel):
    avg_daily_spend: float
    weekly_spend: float
    largest_category: str | None
    largest_category_amount: float
    total_transactions: int


class PlannerSummaryResponseSchema(BaseModel):
    overview: PlannerOverviewSchema
    categories: list[PlannerCategoryAggregateSchema]
    activity: PlannerActivitySchema
    analytics: PlannerAnalyticsMetricsSchema
    generated_at: datetime
    currency: str = "INR"

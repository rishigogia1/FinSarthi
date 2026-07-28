"""
schemas/budgets.py — Validation schemas for category-level budgets.
"""
from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, Field, field_validator, model_validator


class CreateBudgetRequest(BaseModel):
    category: str = Field(..., min_length=1, max_length=100, description="Budget category scope")
    limit_amount: float = Field(..., description="Target spending limit")
    period: Literal["daily", "weekly", "monthly", "yearly"] = Field("monthly", description="Budget cycle period")
    start_date: date = Field(..., description="Budget coverage start date")
    end_date: date | None = Field(None, description="Optional coverage end date")

    @field_validator("limit_amount")
    @classmethod
    def validate_limit(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Limit amount must be greater than zero")
        return v

    @field_validator("category")
    @classmethod
    def clean_category(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Category cannot be blank")
        return stripped

    @model_validator(mode="after")
    def validate_dates(self) -> "CreateBudgetRequest":
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("End date cannot be before start date")
        return self


class UpdateBudgetRequest(BaseModel):
    category: str | None = Field(None, min_length=1, max_length=100)
    limit_amount: float | None = Field(None)
    period: Literal["daily", "weekly", "monthly", "yearly"] | None = Field(None)
    start_date: date | None = Field(None)
    end_date: date | None = Field(None)
    active: bool | None = Field(None)

    @field_validator("limit_amount")
    @classmethod
    def validate_limit(cls, v: float | None) -> float | None:
        if v is not None and v <= 0:
            raise ValueError("Limit amount must be greater than zero")
        return v

    @field_validator("category")
    @classmethod
    def clean_category(cls, v: str | None) -> str | None:
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError("Category cannot be blank")
            return stripped
        return v

    @model_validator(mode="after")
    def validate_dates(self) -> "UpdateBudgetRequest":
        start = self.start_date
        end = self.end_date
        if start is not None and end is not None and end < start:
            raise ValueError("End date cannot be before start date")
        return self


class BudgetResponse(BaseModel):
    id: str
    category: str
    limit_amount: float
    period: str
    start_date: date
    end_date: date | None
    active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        coerce_numbers_to_str = False

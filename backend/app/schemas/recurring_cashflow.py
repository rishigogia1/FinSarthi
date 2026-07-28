"""
schemas/recurring_cashflow.py — Validation schemas for recurring income/expenses.
"""
from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, Field, field_validator, model_validator


class CreateRecurringCashflowRequest(BaseModel):
    type: Literal["income", "expense"] = Field(..., description="Flow type")
    amount: float = Field(..., description="Flow amount")
    category: str = Field(..., min_length=1, max_length=100, description="Flow category")
    frequency: Literal["weekly", "monthly", "yearly"] = Field("monthly", description="Recurrence frequency")
    start_date: date = Field(..., description="Start date of recurrence")
    end_date: date | None = Field(None, description="Optional termination date")
    note: str | None = Field(None, max_length=500, description="Memo note")

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Amount must be greater than zero")
        return v

    @field_validator("category")
    @classmethod
    def clean_category(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Category cannot be blank")
        return stripped

    @field_validator("note")
    @classmethod
    def clean_note(cls, v: str | None) -> str | None:
        if v is not None:
            return v.strip()
        return v

    @model_validator(mode="after")
    def validate_dates(self) -> "CreateRecurringCashflowRequest":
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("End date cannot be before start date")
        return self


class UpdateRecurringCashflowRequest(BaseModel):
    type: Literal["income", "expense"] | None = Field(None)
    amount: float | None = Field(None)
    category: str | None = Field(None, min_length=1, max_length=100)
    frequency: Literal["weekly", "monthly", "yearly"] | None = Field(None)
    start_date: date | None = Field(None)
    end_date: date | None = Field(None)
    active: bool | None = Field(None)
    note: str | None = Field(None, max_length=500)

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: float | None) -> float | None:
        if v is not None and v <= 0:
            raise ValueError("Amount must be greater than zero")
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

    @field_validator("note")
    @classmethod
    def clean_note(cls, v: str | None) -> str | None:
        if v is not None:
            return v.strip()
        return v

    @model_validator(mode="after")
    def validate_dates(self) -> "UpdateRecurringCashflowRequest":
        start = self.start_date
        end = self.end_date
        # Note: In an update request, one or both of start_date/end_date could be None.
        # But if both are provided, we check them. If only end_date is provided, we can check it
        # against the database start_date (which will be validated in the service layer).
        if start is not None and end is not None and end < start:
            raise ValueError("End date cannot be before start date")
        return self


class RecurringCashflowResponse(BaseModel):
    id: str
    type: str
    amount: float
    category: str
    frequency: str
    start_date: date
    end_date: date | None
    active: bool
    note: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        coerce_numbers_to_str = False

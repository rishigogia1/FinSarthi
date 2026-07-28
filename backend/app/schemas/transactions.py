"""
schemas/transactions.py — Validation schemas for financial transactions.
"""
from datetime import date, datetime, timedelta
from typing import Literal
from pydantic import BaseModel, Field, field_validator


class CreateTransactionRequest(BaseModel):
    type: Literal["income", "expense"] = Field(..., description="Transaction type")
    amount: float = Field(..., description="Amount must be greater than zero")
    currency: str = Field("INR", description="Three-letter currency code")
    category: str = Field(..., min_length=1, max_length=100, description="Transaction category classification")
    occurred_on: date = Field(..., description="Date transaction occurred")
    note: str | None = Field(None, max_length=500, description="Optional note memo")
    source: str = Field("MANUAL", description="Source indicator (MANUAL, CHAT, IMPORT, etc.)")

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

    @field_validator("occurred_on")
    @classmethod
    def validate_occurred_on(cls, v: date) -> date:
        if v > date.today() + timedelta(days=366):
            raise ValueError("Occurred date cannot be more than 1 year in the future")
        return v


class UpdateTransactionRequest(BaseModel):
    type: Literal["income", "expense"] | None = Field(None)
    amount: float | None = Field(None)
    currency: str | None = Field(None)
    category: str | None = Field(None, min_length=1, max_length=100)
    occurred_on: date | None = Field(None)
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

    @field_validator("occurred_on")
    @classmethod
    def validate_occurred_on(cls, v: date | None) -> date | None:
        if v is not None:
            if v > date.today() + timedelta(days=366):
                raise ValueError("Occurred date cannot be more than 1 year in the future")
        return v


class TransactionQueryFilter(BaseModel):
    search: str | None = Field(None, description="Search query matching note, category, source, or amount")
    category: str | None = Field(None, description="Category filter")
    type: Literal["income", "expense"] | None = Field(None, description="Transaction type filter")
    start_date: date | None = Field(None, description="Start date filter")
    end_date: date | None = Field(None, description="End date filter")
    min_amount: float | None = Field(None, ge=0, description="Minimum amount filter")
    max_amount: float | None = Field(None, ge=0, description="Maximum amount filter")
    sort_by: Literal["occurred_on", "amount", "created_at", "category"] = Field("occurred_on", description="Field to sort by")
    order: Literal["asc", "desc"] = Field("desc", description="Sort order")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, description="Page size (clamped max 100)")

    @field_validator("page_size")
    @classmethod
    def clamp_page_size(cls, v: int) -> int:
        return min(max(1, v), 100)


class TransactionResponse(BaseModel):
    id: str
    type: str
    amount: float
    currency: str
    category: str
    occurred_on: date
    note: str | None
    source: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class PaginatedTransactionsResponse(BaseModel):
    items: list[TransactionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

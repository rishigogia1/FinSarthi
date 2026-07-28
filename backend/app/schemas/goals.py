"""
schemas/goals.py — Pydantic models for financial goal CRUD validation.
"""
from datetime import date
from typing import Literal
from pydantic import BaseModel, Field, field_validator


class CreateGoalRequest(BaseModel):
    goal_name: str = Field(..., min_length=1, max_length=100, description="Financial goal name")
    target_amount: float = Field(..., description="Target target amount")
    current_amount: float = Field(0.0, description="Current progress savings")
    deadline: date | None = Field(None, description="Deadline target date")

    @field_validator("goal_name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Goal name cannot be empty")
        return stripped

    @field_validator("target_amount")
    @classmethod
    def validate_target(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Target amount must be greater than zero")
        return v

    @field_validator("current_amount")
    @classmethod
    def validate_current(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Current amount must be zero or positive")
        return v

    @field_validator("deadline")
    @classmethod
    def validate_deadline(cls, v: date | None) -> date | None:
        if v is not None and v < date.today():
            raise ValueError("Deadline must be in the future")
        return v


class UpdateGoalRequest(BaseModel):
    goal_name: str | None = Field(None, min_length=1, max_length=100)
    target_amount: float | None = Field(None)
    current_amount: float | None = Field(None)
    deadline: date | None = Field(None)
    status: Literal["active", "completed", "paused"] | None = Field(None)

    @field_validator("goal_name")
    @classmethod
    def clean_name(cls, v: str | None) -> str | None:
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError("Goal name cannot be empty")
            return stripped
        return v

    @field_validator("target_amount")
    @classmethod
    def validate_target(cls, v: float | None) -> float | None:
        if v is not None and v <= 0:
            raise ValueError("Target amount must be greater than zero")
        return v

    @field_validator("current_amount")
    @classmethod
    def validate_current(cls, v: float | None) -> float | None:
        if v is not None and v < 0:
            raise ValueError("Current amount must be zero or positive")
        return v

    @field_validator("deadline")
    @classmethod
    def validate_deadline(cls, v: date | None) -> date | None:
        if v is not None and v < date.today():
            raise ValueError("Deadline must be in the future")
        return v


class GoalResponse(BaseModel):
    id: str
    goal_name: str
    target_amount: float
    current_amount: float
    deadline: date | None
    status: str

    class Config:
        from_attributes = True
        # Numeric values from decimal columns serialize nicely to float in json
        coerce_numbers_to_str = False

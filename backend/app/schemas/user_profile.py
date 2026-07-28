"""
schemas/user_profile.py — Pydantic validation models for user profiles and digital twin properties.
"""
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class UpdateUserProfileRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100, description="Display name of the user")
    income_pattern: str | None = Field(None, max_length=500, description="Income pattern info")
    risk_appetite: str | None = Field(None, max_length=50, description="Risk tolerance profile")
    literacy_level: str | None = Field(None, max_length=50, description="Financial literacy level")
    language_preference: str | None = Field(None, max_length=50, description="Language preference")

    @field_validator("name")
    @classmethod
    def trim_name(cls, v: str | None) -> str | None:
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError("Name cannot be empty or only spaces")
            return stripped
        return v


class UserProfileResponse(BaseModel):
    id: str
    name: str
    email: str
    income_pattern: str | None = None
    risk_appetite: str | None = None
    literacy_level: str | None = None
    language_preference: str | None = None
    onboarding_complete: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

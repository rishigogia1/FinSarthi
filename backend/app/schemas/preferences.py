"""
schemas/preferences.py — Pydantic models for user UI/behavior preferences.
"""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class UpdatePreferencesRequest(BaseModel):
    theme: Literal["light", "dark", "system"] | None = Field(None, description="UI theme style")
    notifications_enabled: bool | None = Field(None, description="Notification active status")


class PreferencesResponse(BaseModel):
    theme: str
    notifications_enabled: bool
    updated_at: datetime

    class Config:
        from_attributes = True

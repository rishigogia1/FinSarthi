"""
schemas/notifications.py — Data validation schemas for user alerts and setting preferences.
"""
from datetime import datetime
from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: str
    title: str
    message: str
    type: str
    read: bool
    archived: bool
    delivery_channel: str
    created_at: datetime


class NotificationListResponse(BaseModel):
    notifications: list[NotificationResponse]


class NotificationPreferenceResponse(BaseModel):
    notifications_enabled: bool


class NotificationPreferenceUpdate(BaseModel):
    notifications_enabled: bool

"""
api/notifications/routes.py — Router for user-scoped alerts and delivery configurations.

All routes require bearer JWT authorization guards.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.user_preference import UserPreference
from app.schemas.notifications import (
    NotificationResponse,
    NotificationListResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate
)
from app.services.notification_service import NotificationService, NotificationServiceError

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def raise_http_exception(e: NotificationServiceError) -> None:
    raise HTTPException(
        status_code=e.status_code,
        detail={
            "error": {
                "code": e.code,
                "message": e.message
            }
        }
    )


@router.get(
    "/",
    response_model=NotificationListResponse
)
async def list_user_notifications(
    include_archived: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> NotificationListResponse:
    """List active notifications feed (optionally including archived alerts)."""
    items = await NotificationService.list_notifications(db, current_user.id, include_archived)
    return NotificationListResponse(notifications=items)


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse
)
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> NotificationResponse:
    """Mark a notification item as read (idempotent operation)."""
    try:
        return await NotificationService.mark_as_read(db, current_user.id, notification_id)
    except NotificationServiceError as e:
        raise_http_exception(e)


@router.patch(
    "/{notification_id}/archive",
    response_model=NotificationResponse
)
async def archive_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> NotificationResponse:
    """Archive a notification alert from user feed."""
    try:
        return await NotificationService.archive_notification(db, current_user.id, notification_id)
    except NotificationServiceError as e:
        raise_http_exception(e)


@router.get(
    "/preferences",
    response_model=NotificationPreferenceResponse
)
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> NotificationPreferenceResponse:
    """Fetch user's multi-channel notification permissions settings."""
    stmt = select(UserPreference).where(UserPreference.user_id == current_user.id)
    res = await db.execute(stmt)
    prefs = res.scalar_one_or_none()
    
    # Lazy initialisation if empty preference record
    if not prefs:
        prefs = UserPreference(user_id=current_user.id, theme="light", notifications_enabled=True)
        db.add(prefs)
        await db.commit()
        
    return NotificationPreferenceResponse(notifications_enabled=prefs.notifications_enabled)


@router.patch(
    "/preferences",
    response_model=NotificationPreferenceResponse
)
async def update_notification_preferences(
    payload: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> NotificationPreferenceResponse:
    """Update user's notification preferences settings."""
    stmt = select(UserPreference).where(UserPreference.user_id == current_user.id)
    res = await db.execute(stmt)
    prefs = res.scalar_one_or_none()
    
    if not prefs:
        prefs = UserPreference(
            user_id=current_user.id,
            theme="light",
            notifications_enabled=payload.notifications_enabled
        )
        db.add(prefs)
    else:
        prefs.notifications_enabled = payload.notifications_enabled
        
    await db.commit()
    return NotificationPreferenceResponse(notifications_enabled=prefs.notifications_enabled)

"""
services/preferences_service.py — Business logic for user preferences configuration.

Handles defaults application, lazy instantiation, and mutations audit logs.
"""
import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.preferences_repository import PreferencesRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.models.user_preference import UserPreference
from app.schemas.preferences import UpdatePreferencesRequest

logger = logging.getLogger(__name__)


class PreferencesService:
    @staticmethod
    async def get_or_create_preferences(session: AsyncSession, user_id: str) -> UserPreference:
        """Fetch preferences, lazy-creating them with default settings if absent."""
        prefs = await PreferencesRepository.get_preferences(session, user_id)
        if not prefs:
            prefs = await PreferencesRepository.create_preferences(
                session,
                user_id=user_id,
                theme="light",
                notifications_enabled=True
            )
            logger.info("Lazy-initialized UserPreference for user_id=%s", user_id)
        return prefs

    @staticmethod
    async def update_preferences(
        session: AsyncSession,
        user_id: str,
        payload: UpdatePreferencesRequest
    ) -> UserPreference:
        """Update preferences and write a synchronous audit trail."""
        prefs = await PreferencesService.get_or_create_preferences(session, user_id)

        before_data = {
            "theme": prefs.theme,
            "notifications_enabled": prefs.notifications_enabled
        }

        # Apply edits
        if payload.theme is not None:
            prefs.theme = payload.theme
        if payload.notifications_enabled is not None:
            prefs.notifications_enabled = payload.notifications_enabled

        prefs.updated_at = datetime.now(timezone.utc)

        after_data = {
            "theme": prefs.theme,
            "notifications_enabled": prefs.notifications_enabled
        }

        # Sync audit log
        await AuditLogRepository.create_audit_log(
            session, user_id, "preferences_updated", before_data, after_data
        )

        logger.info("User preferences updated. user_id=%s", user_id)
        return prefs

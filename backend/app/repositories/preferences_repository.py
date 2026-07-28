"""
repositories/preferences_repository.py — Data access layer for UserPreference model.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user_preference import UserPreference


class PreferencesRepository:
    @staticmethod
    async def get_preferences(session: AsyncSession, user_id: str) -> UserPreference | None:
        """Retrieve the user preferences row."""
        stmt = select(UserPreference).where(UserPreference.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_preferences(
        session: AsyncSession,
        user_id: str,
        theme: str = "light",
        notifications_enabled: bool = True
    ) -> UserPreference:
        """Create a new user preferences row."""
        pref = UserPreference(
            user_id=user_id,
            theme=theme,
            notifications_enabled=notifications_enabled
        )
        session.add(pref)
        await session.flush()
        return pref

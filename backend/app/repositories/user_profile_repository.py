"""
repositories/user_profile_repository.py — Data access layer for User profile and DigitalTwin models.
"""
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.digital_twin import DigitalTwin


class UserProfileRepository:
    @staticmethod
    async def get_digital_twin(session: AsyncSession, user_id: str) -> DigitalTwin | None:
        """Retrieve the digital twin profile for a user."""
        stmt = select(DigitalTwin).where(DigitalTwin.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_digital_twin(session: AsyncSession, user_id: str, **kwargs) -> DigitalTwin:
        """Create a new digital twin profile row for a user."""
        twin = DigitalTwin(user_id=user_id, **kwargs)
        session.add(twin)
        await session.flush()
        return twin

    @staticmethod
    async def update_user_name(session: AsyncSession, user_id: str, name: str) -> User | None:
        """Update display name in users table."""
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(name=name.strip())
            .returning(User)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

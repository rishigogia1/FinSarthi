"""
repositories/user_repository.py — Data access layer for User entity.

Handles email normalization (lowercasing and trimming) at execution time
to guarantee case-insensitive uniqueness constraints.
"""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User


class UserRepository:
    @staticmethod
    async def get_by_email(session: AsyncSession, email: str) -> User | None:
        """Retrieve user by email, case-insensitively."""
        normalized = email.strip().lower()
        stmt = select(User).where(func.lower(User.email) == normalized)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(session: AsyncSession, user_id: str) -> User | None:
        """Retrieve user by UUID id."""
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_user(
        session: AsyncSession,
        name: str,
        email: str,
        password_hash: str
    ) -> User:
        """Create a new user. Normalized email is inserted."""
        normalized_email = email.strip().lower()
        user = User(
            name=name.strip(),
            email=normalized_email,
            password_hash=password_hash
        )
        session.add(user)
        await session.flush()  # Populates user.id and timestamps
        return user

    @staticmethod
    async def exists_by_email(session: AsyncSession, email: str) -> bool:
        """Check if email already exists in users table, case-insensitively."""
        user = await UserRepository.get_by_email(session, email)
        return user is not None

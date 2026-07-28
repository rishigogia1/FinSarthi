"""
repositories/refresh_token_repository.py — Data access layer for RefreshToken entity.

Handles token hashes for lookup, token creation, and revocation.
"""
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    @staticmethod
    async def create_token(
        session: AsyncSession,
        user_id: str,
        token_hash: str,
        expires_at: datetime
    ) -> RefreshToken:
        """Store a new refresh token hash in the database."""
        token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            revoked=False
        )
        session.add(token)
        await session.flush()
        return token

    @staticmethod
    async def get_by_token_hash(
        session: AsyncSession,
        token_hash: str
    ) -> RefreshToken | None:
        """Look up a token record by its hashed representation."""
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def revoke_token(session: AsyncSession, token_id: str) -> None:
        """Mark a specific refresh token as revoked."""
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.id == token_id)
            .values(revoked=True)
        )
        await session.execute(stmt)

    @staticmethod
    async def revoke_all_for_user(session: AsyncSession, user_id: str) -> None:
        """
        Revoke all active refresh tokens for a user.
        Enforces the V1 'one active refresh token per user' policy.
        """
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .where(RefreshToken.revoked == False)  # noqa: E712
            .values(revoked=True)
        )
        await session.execute(stmt)

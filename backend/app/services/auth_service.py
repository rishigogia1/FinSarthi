"""
services/auth_service.py — Business logic layer for identity, session, and token management.

Coordinates repositories and core/security.py. Raises domain-specific exceptions.
Enforces the V1 single active refresh token policy.
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core import security
from app.repositories.user_repository import UserRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.models.user import User

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Domain Exceptions
# ---------------------------------------------------------------------------
class AuthServiceError(Exception):
    """Base exception for authentication service errors."""

    def __init__(self, code: str, message: str, status_code: int = 401):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class DuplicateEmailError(AuthServiceError):
    def __init__(self, message: str = "Email already registered"):
        super().__init__("duplicate_email", message, status_code=409)


class InvalidCredentialsError(AuthServiceError):
    def __init__(self, message: str = "Invalid email or password"):
        super().__init__("invalid_credentials", message, status_code=401)


class TokenExpiredError(AuthServiceError):
    def __init__(self, message: str = "Token has expired"):
        super().__init__("token_expired", message, status_code=401)


class TokenRevokedError(AuthServiceError):
    def __init__(self, message: str = "Token has been revoked"):
        super().__init__("token_revoked", message, status_code=401)


class UserNotFoundError(AuthServiceError):
    def __init__(self, message: str = "User not found"):
        super().__init__("user_not_found", message, status_code=401)


# ---------------------------------------------------------------------------
# AuthService Implementation
# ---------------------------------------------------------------------------
class AuthService:
    @staticmethod
    async def register(
        session: AsyncSession,
        name: str,
        email: str,
        password: str,
    ) -> tuple[User, str, str]:
        """
        Register a new user, issue initial access/refresh tokens.
        Raises DuplicateEmailError.
        """
        if await UserRepository.exists_by_email(session, email):
            raise DuplicateEmailError()

        password_hash = security.hash_password(password)
        user = await UserRepository.create_user(session, name, email, password_hash)

        access_token = security.create_access_token(user.id)
        raw_refresh = security.generate_refresh_token()
        hashed_refresh = security.hash_token(raw_refresh)

        # Store UTC timestamp as a naive datetime (matches PostgreSQL TIMESTAMP WITHOUT TIME ZONE)
        user.last_login_at = datetime.utcnow()

        expires_at = datetime.utcnow() + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )

        await RefreshTokenRepository.create_token(
            session,
            user.id,
            hashed_refresh,
            expires_at,
        )

        logger.info(
            "User registered successfully. id=%s, domain=%s",
            user.id,
            email.split("@")[-1],
        )

        return user, access_token, raw_refresh

    @staticmethod
    async def login(
        session: AsyncSession,
        email: str,
        password: str,
    ) -> tuple[User, str, str]:
        """
        Authenticate user credentials, rotate refresh tokens.
        Raises InvalidCredentialsError.
        """
        user = await UserRepository.get_by_email(session, email)

        if not user:
            security.verify_password(
                password,
                "$2b$12$DummySaltValueDummySaltValueDummySaltValue",
            )
            raise InvalidCredentialsError()

        if not security.verify_password(password, user.password_hash):
            raise InvalidCredentialsError()

        await RefreshTokenRepository.revoke_all_for_user(session, user.id)

        access_token = security.create_access_token(user.id)
        raw_refresh = security.generate_refresh_token()
        hashed_refresh = security.hash_token(raw_refresh)

        # Store UTC timestamp as a naive datetime (matches PostgreSQL TIMESTAMP WITHOUT TIME ZONE)
        user.last_login_at = datetime.utcnow()

        expires_at = datetime.utcnow() + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )

        await RefreshTokenRepository.create_token(
            session,
            user.id,
            hashed_refresh,
            expires_at,
        )

        logger.info("User login successful. id=%s", user.id)

        return user, access_token, raw_refresh

    @staticmethod
    async def refresh(
        session: AsyncSession,
        raw_refresh_token: str,
    ) -> tuple[str, str]:
        """
        Verify the opaque refresh token, perform rotation (revoke old, issue new).
        Raises TokenRevokedError, TokenExpiredError, or InvalidCredentialsError.
        """
        hashed_token = security.hash_token(raw_refresh_token)

        token_record = await RefreshTokenRepository.get_by_token_hash(
            session,
            hashed_token,
        )

        if not token_record:
            raise InvalidCredentialsError("Invalid refresh token")

        if token_record.revoked:
            await RefreshTokenRepository.revoke_all_for_user(
                session,
                token_record.user_id,
            )
            raise TokenRevokedError("Refresh token has been revoked")

        expires_at = token_record.expires_at
        cmp_now = datetime.now(expires_at.tzinfo) if expires_at.tzinfo else datetime.utcnow()

        if expires_at < cmp_now:
            raise TokenExpiredError("Refresh token has expired")

        await RefreshTokenRepository.revoke_token(
            session,
            token_record.id,
        )

        new_access_token = security.create_access_token(token_record.user_id)
        new_raw_refresh = security.generate_refresh_token()
        new_hashed_refresh = security.hash_token(new_raw_refresh)

        new_expires_at = datetime.utcnow() + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )

        await RefreshTokenRepository.create_token(
            session,
            token_record.user_id,
            new_hashed_refresh,
            new_expires_at,
        )

        logger.info(
            "Refresh token rotated successfully for user=%s",
            token_record.user_id,
        )

        return new_access_token, new_raw_refresh

    @staticmethod
    async def logout(
        session: AsyncSession,
        raw_refresh_token: str,
    ) -> None:
        """
        Revoke the refresh token on user logout.
        Raises InvalidCredentialsError if token is invalid or already revoked.
        """
        hashed_token = security.hash_token(raw_refresh_token)

        token_record = await RefreshTokenRepository.get_by_token_hash(
            session,
            hashed_token,
        )

        if not token_record:
            raise InvalidCredentialsError("Invalid refresh token")

        if token_record.revoked:
            raise TokenRevokedError("Token already revoked")

        await RefreshTokenRepository.revoke_token(
            session,
            token_record.id,
        )

        logger.info(
            "Refresh token revoked successfully on logout. user=%s",
            token_record.user_id,
        )

    @staticmethod
    async def get_current_user(
        session: AsyncSession,
        access_token: str,
    ) -> User:
        """
        Resolve user from a decoded access token.
        Raises TokenExpiredError, InvalidTokenError, or UserNotFoundError.
        """
        try:
            payload = security.decode_access_token(access_token)
        except security.TokenExpiredError as e:
            raise TokenExpiredError(str(e))
        except security.InvalidTokenError as e:
            raise TokenRevokedError(str(e))

        user_id = payload.get("sub")

        if not user_id:
            raise InvalidCredentialsError("Access token is missing 'sub'")

        user = await UserRepository.get_by_id(session, user_id)

        if not user:
            raise UserNotFoundError()

        return user
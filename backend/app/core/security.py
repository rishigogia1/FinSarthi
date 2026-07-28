"""
core/security.py — Cryptographic helper functions for password hashing and JWT management.

Uses bcrypt for password hashing and PyJWT for access tokens.
Refresh tokens are opaque random strings hashed with SHA-256 before DB storage.
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
from app.core.config import settings

class SecurityError(Exception):
    """Base exception for security operations."""
    pass

class TokenExpiredError(SecurityError):
    """Raised when a JWT has expired."""
    pass

class InvalidTokenError(SecurityError):
    """Raised when a JWT is malformed, invalid, or has the wrong type."""
    pass

def hash_password(plain_password: str) -> str:
    """Hash a plain text password using bcrypt."""
    salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against a bcrypt hash in constant time."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False

def generate_refresh_token() -> str:
    """Generate a high-entropy opaque random refresh token."""
    return secrets.token_urlsafe(48)

def hash_token(raw_token: str) -> str:
    """Hash an opaque token using SHA-256 for secure DB storage."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

def create_access_token(user_id: str, expires_delta: timedelta | None = None) -> str:
    """Create a short-lived JWT access token."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp())
    }
    
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT access token.
    Raises TokenExpiredError or InvalidTokenError.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("type") != "access":
            raise InvalidTokenError("Token is not an access token")
        return payload
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError("Access token has expired")
    except jwt.InvalidTokenError as e:
        raise InvalidTokenError(str(e))

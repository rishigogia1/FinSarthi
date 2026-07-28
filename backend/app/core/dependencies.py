"""
dependencies.py — FastAPI dependency injection wiring.

Provides application-wide dependencies:
  1. get_db: provides active database AsyncSession.
  2. get_current_user: verifies JWT and retrieves matching User.
"""
from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.services.auth_service import AuthService, AuthServiceError

# Token URL corresponds to our login endpoint prefix
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency guard to ensure the request has a valid access token.
    Resolves to the current authenticated User.
    """
    try:
        return await AuthService.get_current_user(db, token)
    except AuthServiceError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message
                }
            }
        )

__all__ = ["get_db", "get_current_user"]

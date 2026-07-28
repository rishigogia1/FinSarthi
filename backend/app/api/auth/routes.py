"""
api/auth/routes.py — Router for all authentication and session management endpoints.

Endpoints implemented:
  - POST /api/v1/auth/register
  - POST /api/v1/auth/login
  - POST /api/v1/auth/refresh
  - POST /api/v1/auth/logout
  - GET /api/v1/auth/me
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_db, get_current_user
from app.core.rate_limit import RateLimiter
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    RefreshTokenRequest,
    LogoutRequest,
    AuthUserResponse,
    TokenPairResponse,
    AuthResponse,
    LogoutResponse,
)
from app.services.auth_service import AuthService, AuthServiceError

router = APIRouter(prefix="/auth", tags=["Authentication"])

def raise_http_exception(e: AuthServiceError) -> None:
    """Helper to convert AuthServiceError domain exceptions to FastAPI HTTPExceptions."""
    raise HTTPException(
        status_code=e.status_code,
        detail={
            "error": {
                "code": e.code,
                "message": e.message
            }
        }
    )


# Rate limiters configured with values from app/core/config.py
register_limiter = RateLimiter("register", settings.AUTH_RATE_LIMIT_REGISTER, settings.AUTH_RATE_LIMIT_WINDOW_SECONDS)
login_limiter = RateLimiter("login", settings.AUTH_RATE_LIMIT_LOGIN, settings.AUTH_RATE_LIMIT_WINDOW_SECONDS)
refresh_limiter = RateLimiter("refresh", settings.AUTH_RATE_LIMIT_REFRESH, settings.AUTH_RATE_LIMIT_WINDOW_SECONDS)


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=201,
    dependencies=[Depends(register_limiter)]
)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db)
) -> AuthResponse:
    """Register a new user and return user info + initial token pair."""
    try:
        user, access_token, raw_refresh = await AuthService.register(
            db, payload.name, payload.email, payload.password
        )
        # Commit to persist the changes
        await db.commit()
    except AuthServiceError as e:
        await db.rollback()
        raise_http_exception(e)

    expires_in = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    return AuthResponse(
        user=AuthUserResponse.model_validate(user),
        tokens=TokenPairResponse(
            access_token=access_token,
            refresh_token=raw_refresh,
            expires_in=expires_in
        )
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    dependencies=[Depends(login_limiter)]
)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> AuthResponse:
    """Authenticate credentials and issue a new token pair (rotates refresh token)."""
    try:
        user, access_token, raw_refresh = await AuthService.login(
            db, payload.email, payload.password
        )
        await db.commit()
    except AuthServiceError as e:
        await db.rollback()
        raise_http_exception(e)

    expires_in = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    return AuthResponse(
        user=AuthUserResponse.model_validate(user),
        tokens=TokenPairResponse(
            access_token=access_token,
            refresh_token=raw_refresh,
            expires_in=expires_in
        )
    )


@router.post(
    "/refresh",
    response_model=TokenPairResponse,
    dependencies=[Depends(refresh_limiter)]
)
async def refresh(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
) -> TokenPairResponse:
    """Rotate the opaque refresh token, invalidating the old one and returning a new pair."""
    try:
        access_token, raw_refresh = await AuthService.refresh(
            db, payload.refresh_token
        )
        await db.commit()
    except AuthServiceError as e:
        await db.rollback()
        raise_http_exception(e)

    expires_in = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    return TokenPairResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        expires_in=expires_in
    )


@router.post(
    "/logout",
    response_model=LogoutResponse
)
async def logout(
    payload: LogoutRequest,
    db: AsyncSession = Depends(get_db)
) -> LogoutResponse:
    """Revoke a refresh token so it cannot be used again."""
    try:
        await AuthService.logout(db, payload.refresh_token)
        await db.commit()
    except AuthServiceError as e:
        await db.rollback()
        raise_http_exception(e)

    return LogoutResponse(success=True)


@router.get(
    "/me",
    response_model=AuthUserResponse
)
async def me(
    current_user: User = Depends(get_current_user)
) -> AuthUserResponse:
    """Get profile information for the currently authenticated user."""
    return AuthUserResponse.model_validate(current_user)

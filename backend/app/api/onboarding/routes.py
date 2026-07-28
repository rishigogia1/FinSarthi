"""
api/onboarding/routes.py — Router for user onboarding flow tracking endpoints.

Protected by Bearer JWT authorization.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.onboarding import (
    OnboardingStatusResponse,
    OnboardingCompleteRequest
)
from app.services.onboarding_service import OnboardingService

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


@router.get(
    "/status",
    response_model=OnboardingStatusResponse
)
async def get_onboarding_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> OnboardingStatusResponse:
    """Fetch current onboarding status and step completion indicators."""
    return await OnboardingService.get_onboarding_status(db, current_user.id)


@router.post(
    "/complete",
    response_model=OnboardingStatusResponse
)
async def complete_onboarding(
    payload: OnboardingCompleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> OnboardingStatusResponse:
    """Toggle manual completed flag for user onboarding flow."""
    success = await OnboardingService.complete_onboarding(db, current_user.id, payload.completed)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User record not found."
        )
    return await OnboardingService.get_onboarding_status(db, current_user.id)


@router.get(
    "/steps",
    response_model=OnboardingStatusResponse
)
async def get_onboarding_steps(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> OnboardingStatusResponse:
    """Alias for /status to return the checklist of onboarding steps."""
    return await OnboardingService.get_onboarding_status(db, current_user.id)

"""
api/users/routes.py — Router for user-specific endpoints: profiles, goals, preferences, onboarding.

All endpoints are protected by the JWT authentication dependency guard.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.user_profile import UserProfileResponse, UpdateUserProfileRequest
from app.schemas.preferences import PreferencesResponse, UpdatePreferencesRequest
from app.schemas.goals import GoalResponse, CreateGoalRequest, UpdateGoalRequest
from app.services.user_profile_service import UserProfileService, ProfileServiceError
from app.services.preferences_service import PreferencesService
from app.services.goals_service import GoalsService
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/users", tags=["User Profiles & Preferences"])


def raise_http_exception(e: ProfileServiceError) -> None:
    """Helper to convert ProfileServiceError domain exceptions to FastAPI HTTPExceptions."""
    raise HTTPException(
        status_code=e.status_code,
        detail={
            "error": {
                "code": e.code,
                "message": e.message
            }
        }
    )


@router.get(
    "/me",
    response_model=UserProfileResponse
)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserProfileResponse:
    """Get the current authenticated user's profile and digital twin details."""
    try:
        user, twin = await UserProfileService.get_or_create_profile(db, current_user.id)
    except ProfileServiceError as e:
        raise_http_exception(e)

    # Resolve onboarding complete from behavioral_notes dict
    onboarding_complete = False
    if twin.behavioral_notes:
        onboarding_complete = twin.behavioral_notes.get("onboarding_complete", False)

    return UserProfileResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        income_pattern=twin.income_pattern,
        risk_appetite=twin.risk_appetite,
        literacy_level=twin.literacy_level,
        language_preference=twin.language_preference,
        onboarding_complete=onboarding_complete,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@router.patch(
    "/me",
    response_model=UserProfileResponse
)
async def update_me(
    payload: UpdateUserProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserProfileResponse:
    """Update editable profile fields on current user profile, writing to audit log."""
    try:
        user, twin = await UserProfileService.update_profile(db, current_user.id, payload)
        await db.commit()
    except ProfileServiceError as e:
        await db.rollback()
        raise_http_exception(e)

    onboarding_complete = False
    if twin.behavioral_notes:
        onboarding_complete = twin.behavioral_notes.get("onboarding_complete", False)

    return UserProfileResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        income_pattern=twin.income_pattern,
        risk_appetite=twin.risk_appetite,
        literacy_level=twin.literacy_level,
        language_preference=twin.language_preference,
        onboarding_complete=onboarding_complete,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@router.get(
    "/me/preferences",
    response_model=PreferencesResponse
)
async def get_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PreferencesResponse:
    """Get preferences for the current user (lazy-created if missing)."""
    try:
        prefs = await PreferencesService.get_or_create_preferences(db, current_user.id)
    except ProfileServiceError as e:
        raise_http_exception(e)

    return PreferencesResponse.model_validate(prefs)


@router.patch(
    "/me/preferences",
    response_model=PreferencesResponse
)
async def update_preferences(
    payload: UpdatePreferencesRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PreferencesResponse:
    """Update preferences for the current user, logging changes to audit log."""
    try:
        prefs = await PreferencesService.update_preferences(db, current_user.id, payload)
        await db.commit()
    except ProfileServiceError as e:
        await db.rollback()
        raise_http_exception(e)

    return PreferencesResponse.model_validate(prefs)


@router.get(
    "/me/goals",
    response_model=list[GoalResponse]
)
async def list_goals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> list[GoalResponse]:
    """List financial goals belonging strictly to the current user."""
    try:
        goals = await GoalsService.list_goals(db, current_user.id)
    except ProfileServiceError as e:
        raise_http_exception(e)

    return [GoalResponse.model_validate(g) for g in goals]


@router.post(
    "/me/goals",
    response_model=GoalResponse,
    status_code=201
)
async def create_goal(
    payload: CreateGoalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> GoalResponse:
    """Create a new financial goal for the current user."""
    try:
        goal = await GoalsService.create_goal(db, current_user.id, payload)
        await db.commit()
    except ProfileServiceError as e:
        await db.rollback()
        raise_http_exception(e)

    return GoalResponse.model_validate(goal)


@router.patch(
    "/me/goals/{goal_id}",
    response_model=GoalResponse
)
async def update_goal(
    goal_id: str,
    payload: UpdateGoalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> GoalResponse:
    """Update an owned financial goal, checking permissions and logging to audit log."""
    try:
        goal = await GoalsService.update_goal(db, current_user.id, goal_id, payload)
        await db.commit()
    except ProfileServiceError as e:
        await db.rollback()
        raise_http_exception(e)

    return GoalResponse.model_validate(goal)


@router.delete(
    "/me/goals/{goal_id}",
    status_code=204
)
async def delete_goal(
    goal_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a financial goal, enforcing ownership and logging to audit log."""
    try:
        await GoalsService.delete_goal(db, current_user.id, goal_id)
        await db.commit()
    except ProfileServiceError as e:
        await db.rollback()
        raise_http_exception(e)


@router.post(
    "/me/onboarding/complete",
    response_model=UserProfileResponse
)
async def complete_onboarding(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserProfileResponse:
    """Verify onboarding parameters and mark onboarding complete."""
    try:
        twin = await UserProfileService.complete_onboarding(db, current_user.id)
        user = await UserRepository.get_by_id(db, current_user.id)
        await db.commit()
    except ProfileServiceError as e:
        await db.rollback()
        raise_http_exception(e)

    onboarding_complete = False
    if twin.behavioral_notes:
        onboarding_complete = twin.behavioral_notes.get("onboarding_complete", False)

    return UserProfileResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        income_pattern=twin.income_pattern,
        risk_appetite=twin.risk_appetite,
        literacy_level=twin.literacy_level,
        language_preference=twin.language_preference,
        onboarding_complete=onboarding_complete,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

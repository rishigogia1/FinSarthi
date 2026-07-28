"""
services/user_profile_service.py — Business logic for user profiles, digital twins, and onboarding.

Coordinates repositories and handles lazy initialization of twin profiles, validation of onboarding,
and synchronous audit logs.
"""
import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repository import UserRepository
from app.repositories.user_profile_repository import UserProfileRepository
from app.repositories.preferences_repository import PreferencesRepository
from app.repositories.goals_repository import GoalsRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.models.user import User
from app.models.digital_twin import DigitalTwin
from app.schemas.user_profile import UpdateUserProfileRequest

logger = logging.getLogger(__name__)


class ProfileServiceError(Exception):
    """Base exception for profile and onboarding errors."""
    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class ProfileUserNotFoundError(ProfileServiceError):
    def __init__(self):
        super().__init__("user_not_found", "User not found", status_code=404)


class OnboardingCriteriaNotMetError(ProfileServiceError):
    def __init__(self, message: str = "Onboarding criteria not met"):
        super().__init__("onboarding_criteria_not_met", message, status_code=400)


class UserProfileService:
    @staticmethod
    async def get_or_create_profile(session: AsyncSession, user_id: str) -> tuple[User, DigitalTwin]:
        """Retrieve user and digital twin. Lazy creates the digital twin if not yet initialized."""
        user = await UserRepository.get_by_id(session, user_id)
        if not user:
            raise ProfileUserNotFoundError()

        twin = await UserProfileRepository.get_digital_twin(session, user_id)
        if not twin:
            # Lazy initialize the digital twin record
            twin = await UserProfileRepository.create_digital_twin(
                session,
                user_id=user_id,
                accessibility_needs={},
                behavioral_notes={}
            )
            logger.info("Lazy-initialized DigitalTwin for user_id=%s", user_id)
        
        return user, twin

    @staticmethod
    async def update_profile(
        session: AsyncSession,
        user_id: str,
        payload: UpdateUserProfileRequest
    ) -> tuple[User, DigitalTwin]:
        """Update display name and twin parameters, generating a synchronous audit log."""
        user, twin = await UserProfileService.get_or_create_profile(session, user_id)

        # Store before-state for non-repudiation auditing
        before_data = {
            "name": user.name,
            "income_pattern": twin.income_pattern,
            "risk_appetite": twin.risk_appetite,
            "literacy_level": twin.literacy_level,
            "language_preference": twin.language_preference
        }

        # Apply updates
        if payload.name is not None:
            await UserProfileRepository.update_user_name(session, user_id, payload.name)
            # Refresh memory object
            user.name = payload.name.strip()

        if payload.income_pattern is not None:
            twin.income_pattern = payload.income_pattern.strip()
        if payload.risk_appetite is not None:
            twin.risk_appetite = payload.risk_appetite.strip()
        if payload.literacy_level is not None:
            twin.literacy_level = payload.literacy_level.strip()
        if payload.language_preference is not None:
            twin.language_preference = payload.language_preference.strip()

        twin.updated_at = datetime.now(timezone.utc)

        after_data = {
            "name": user.name,
            "income_pattern": twin.income_pattern,
            "risk_appetite": twin.risk_appetite,
            "literacy_level": twin.literacy_level,
            "language_preference": twin.language_preference
        }

        # Synchronous audit log
        await AuditLogRepository.create_audit_log(
            session, user_id, "profile_updated", before_data, after_data
        )

        logger.info("User profile updated. user_id=%s", user_id)
        return user, twin

    @staticmethod
    async def complete_onboarding(session: AsyncSession, user_id: str) -> DigitalTwin:
        """
        Mark onboarding complete if requirements are met.
        Criteria: name set, at least one twin detail present, at least one goal/customized preference set.
        """
        user, twin = await UserProfileService.get_or_create_profile(session, user_id)

        # 1. Name validation
        if not user.name or not user.name.strip():
            raise OnboardingCriteriaNotMetError("Display name is required for onboarding")

        # 2. At least one twin detail
        has_detail = any([
            twin.income_pattern,
            twin.risk_appetite,
            twin.literacy_level,
            twin.language_preference
        ])
        if not has_detail:
            raise OnboardingCriteriaNotMetError("At least one profile parameter must be completed")

        # 3. Goal exists or preference customized
        goals = await GoalsRepository.get_user_goals(session, user_id)
        has_goal = len(goals) > 0

        prefs = await PreferencesRepository.get_preferences(session, user_id)
        has_custom_pref = False
        if prefs:
            has_custom_pref = (prefs.theme != "light" or not prefs.notifications_enabled)

        if not (has_goal or has_custom_pref):
            raise OnboardingCriteriaNotMetError("Please set up at least one financial goal or customize your preferences to complete onboarding")

        # Validation passed — update onboarding status
        before_notes = twin.behavioral_notes or {}
        new_notes = {**before_notes, "onboarding_complete": True}
        twin.behavioral_notes = new_notes
        twin.updated_at = datetime.now(timezone.utc)

        # Sync audit log
        await AuditLogRepository.create_audit_log(
            session, user_id, "onboarding_completed", before_notes, new_notes
        )

        logger.info("User completed onboarding successfully. user_id=%s", user_id)
        return twin

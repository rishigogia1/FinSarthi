"""
services/goals_service.py — Business logic for financial goals.

Enforces strict user ownership checks and writes synchronous audit trails for all CRUD mutations.
"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.goals_repository import GoalsRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.models.goal import Goal
from app.schemas.goals import CreateGoalRequest, UpdateGoalRequest
from app.services.user_profile_service import ProfileServiceError

logger = logging.getLogger(__name__)


class GoalNotFoundError(ProfileServiceError):
    def __init__(self):
        super().__init__("goal_not_found", "Goal not found", status_code=404)


class GoalOwnershipViolationError(ProfileServiceError):
    def __init__(self):
        super().__init__("forbidden", "You do not own this resource", status_code=403)


class GoalsService:
    @staticmethod
    async def create_goal(
        session: AsyncSession,
        user_id: str,
        payload: CreateGoalRequest
    ) -> Goal:
        """Create a new goal for the authenticated user and write an audit log."""
        goal = await GoalsRepository.create_goal(
            session,
            user_id=user_id,
            goal_name=payload.goal_name,
            target_amount=payload.target_amount,
            current_amount=payload.current_amount,
            deadline=payload.deadline,
            status="active"
        )

        after_data = {
            "id": goal.id,
            "goal_name": goal.goal_name,
            "target_amount": float(goal.target_amount),
            "current_amount": float(goal.current_amount),
            "deadline": str(goal.deadline) if goal.deadline else None,
            "status": goal.status
        }

        # Sync audit log
        await AuditLogRepository.create_audit_log(
            session, user_id, "goal_created", before=None, after=after_data
        )

        logger.info("Goal created successfully. user_id=%s, goal_id=%s", user_id, goal.id)
        return goal

    @staticmethod
    async def list_goals(session: AsyncSession, user_id: str) -> list[Goal]:
        """List only the goals belonging to the authenticated user."""
        return await GoalsRepository.get_user_goals(session, user_id)

    @staticmethod
    async def update_goal(
        session: AsyncSession,
        user_id: str,
        goal_id: str,
        payload: UpdateGoalRequest
    ) -> Goal:
        """Update a user's goal, verifying ownership and writing a synchronous audit log."""
        goal = await GoalsRepository.get_goal(session, goal_id)
        if not goal:
            raise GoalNotFoundError()

        # Enforce strict user ownership boundary
        if goal.user_id != user_id:
            raise GoalOwnershipViolationError()

        before_data = {
            "goal_name": goal.goal_name,
            "target_amount": float(goal.target_amount),
            "current_amount": float(goal.current_amount),
            "deadline": str(goal.deadline) if goal.deadline else None,
            "status": goal.status
        }

        # Apply edits
        if payload.goal_name is not None:
            goal.goal_name = payload.clean_name(payload.goal_name)
        if payload.target_amount is not None:
            goal.target_amount = payload.target_amount
        if payload.current_amount is not None:
            goal.current_amount = payload.current_amount
        if payload.deadline is not None:
            goal.deadline = payload.deadline
        if payload.status is not None:
            goal.status = payload.status

        after_data = {
            "goal_name": goal.goal_name,
            "target_amount": float(goal.target_amount),
            "current_amount": float(goal.current_amount),
            "deadline": str(goal.deadline) if goal.deadline else None,
            "status": goal.status
        }

        # Sync audit log
        await AuditLogRepository.create_audit_log(
            session, user_id, "goal_updated", before_data, after_data
        )

        logger.info("Goal updated. user_id=%s, goal_id=%s", user_id, goal.id)
        return goal

    @staticmethod
    async def delete_goal(session: AsyncSession, user_id: str, goal_id: str) -> None:
        """Delete a user's goal, verifying ownership and logging to audit log."""
        goal = await GoalsRepository.get_goal(session, goal_id)
        if not goal:
            raise GoalNotFoundError()

        # Enforce strict user ownership boundary
        if goal.user_id != user_id:
            raise GoalOwnershipViolationError()

        before_data = {
            "id": goal.id,
            "goal_name": goal.goal_name,
            "target_amount": float(goal.target_amount),
            "current_amount": float(goal.current_amount),
            "deadline": str(goal.deadline) if goal.deadline else None,
            "status": goal.status
        }

        await GoalsRepository.delete_goal(session, goal_id)

        # Sync audit log
        await AuditLogRepository.create_audit_log(
            session, user_id, "goal_deleted", before_data, after=None
        )

        logger.info("Goal deleted. user_id=%s, goal_id=%s", user_id, goal_id)

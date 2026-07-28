"""
services/onboarding_service.py — Service managing onboarding step evaluation.
"""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.models.import_job import ImportJob
from app.schemas.onboarding import OnboardingStatusResponse, OnboardingStepResponse
from app.repositories.audit_log_repository import AuditLogRepository


class OnboardingService:
    @staticmethod
    async def get_onboarding_status(session: AsyncSession, user_id: str) -> OnboardingStatusResponse:
        """Evaluate current onboarding checklist steps based on user data."""
        # 1. Fetch user onboarding status
        stmt = select(User).where(User.id == user_id)
        res = await session.execute(stmt)
        user = res.scalar_one()

        # 2. Check if user has added transactions
        t_stmt = select(func.count(Transaction.id)).where(Transaction.user_id == user_id)
        t_res = await session.execute(t_stmt)
        has_transactions = (t_res.scalar() or 0) > 0

        # 3. Check if user has import jobs
        ij_stmt = select(func.count(ImportJob.id)).where(ImportJob.user_id == user_id)
        ij_res = await session.execute(ij_stmt)
        has_imports = (ij_res.scalar() or 0) > 0

        # 4. Check if user has budgets
        b_stmt = select(func.count(Budget.id)).where(Budget.user_id == user_id)
        b_res = await session.execute(b_stmt)
        has_budgets = (b_res.scalar() or 0) > 0

        steps = [
            OnboardingStepResponse(
                step_id="add_transaction",
                title="Add a Transaction",
                description="Manually create your first transaction record.",
                completed=has_transactions
            ),
            OnboardingStepResponse(
                step_id="upload_csv",
                title="Upload CSV Statements",
                description="Import transactions from a banking CSV file.",
                completed=has_imports
            ),
            OnboardingStepResponse(
                step_id="configure_budget",
                title="Create a Budget",
                description="Set monthly limit guidelines on groceries, dining, etc.",
                completed=has_budgets
            ),
            OnboardingStepResponse(
                step_id="check_insights",
                title="Review Insights & AI Recommendations",
                description="Open insights panel to view forecasts and explanations.",
                completed=user.onboarding_completed  # Completed once they toggle onboarding finished
            )
        ]

        # Onboarding is completed if marked true explicitly or if all steps are completed
        auto_completed = has_transactions and has_imports and has_budgets and user.onboarding_completed
        completed_flag = user.onboarding_completed or auto_completed

        return OnboardingStatusResponse(
            onboarding_completed=completed_flag,
            steps=steps
        )

    @staticmethod
    async def complete_onboarding(session: AsyncSession, user_id: str, completed: bool) -> bool:
        """Mark user onboarding flow as finished and write audit record."""
        stmt = select(User).where(User.id == user_id)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            return False

        if user.onboarding_completed != completed:
            user.onboarding_completed = completed
            await AuditLogRepository.create_audit_log(
                session=session,
                user_id=user_id,
                action="user.onboarding_completed",
                before={"onboarding_completed": not completed},
                after={"onboarding_completed": completed}
            )
            await session.commit()
        return True

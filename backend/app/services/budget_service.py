"""
services/budget_service.py — Business logic for category budgets.

Enforces range bounds, active budget overlap collisions checking, ownership validation, and audit tracking.
"""
import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.budget_repository import BudgetRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.models.budget import Budget
from app.schemas.budgets import CreateBudgetRequest, UpdateBudgetRequest
from app.services.transaction_service import FinanceServiceError

logger = logging.getLogger(__name__)


class BudgetNotFoundError(FinanceServiceError):
    def __init__(self):
        super().__init__("budget_not_found", "Budget not found", status_code=404)


class BudgetService:
    @staticmethod
    async def create_budget(
        session: AsyncSession,
        user_id: str,
        payload: CreateBudgetRequest
    ) -> Budget:
        """Create a budget, checking for overlaps and recording audit log."""
        # 1. Enforce overlapping budgets rule
        overlaps = await BudgetRepository.get_active_overlapping_budgets(
            session=session,
            user_id=user_id,
            category=payload.category,
            start_date=payload.start_date,
            end_date=payload.end_date
        )
        if overlaps:
            raise FinanceServiceError(
                code="budget_overlap",
                message="An active budget already exists for this category during this period",
                status_code=400
            )

        budget = await BudgetRepository.create_budget(
            session=session,
            user_id=user_id,
            category=payload.category,
            limit_amount=payload.limit_amount,
            period=payload.period,
            start_date=payload.start_date,
            end_date=payload.end_date,
            active=True
        )

        after_data = {
            "id": budget.id,
            "category": budget.category,
            "limit_amount": float(budget.limit_amount),
            "period": budget.period,
            "start_date": str(budget.start_date),
            "end_date": str(budget.end_date) if budget.end_date else None,
            "active": budget.active
        }

        await AuditLogRepository.create_audit_log(
            session=session,
            user_id=user_id,
            action="budget.created",
            before=None,
            after=after_data
        )

        logger.info("Budget created. user_id=%s, budget_id=%s", user_id, budget.id)
        return budget

    @staticmethod
    async def list_budgets(session: AsyncSession, user_id: str) -> list[Budget]:
        """List budgets belonging to user."""
        return await BudgetRepository.list_user_budgets(session, user_id)

    @staticmethod
    async def get_budget(
        session: AsyncSession,
        user_id: str,
        budget_id: str
    ) -> Budget:
        """Retrieve a specific budget, enforcing ownership."""
        b = await BudgetRepository.get_user_budget(session, user_id, budget_id)
        if not b:
            raise BudgetNotFoundError()
        return b

    @staticmethod
    async def update_budget(
        session: AsyncSession,
        user_id: str,
        budget_id: str,
        payload: UpdateBudgetRequest
    ) -> Budget:
        """Update an owned budget, verifying overlap collision constraints and writing audit log."""
        b = await BudgetRepository.get_user_budget(session, user_id, budget_id)
        if not b:
            raise BudgetNotFoundError()

        # Resolve properties for validity checks
        new_category = payload.category if payload.category is not None else b.category
        new_start = payload.start_date if payload.start_date is not None else b.start_date
        new_end = payload.end_date if payload.end_date is not None else b.end_date
        new_active = payload.active if payload.active is not None else b.active

        # 1. Enforce start/end bounds check
        if new_end is not None and new_end < new_start:
            raise FinanceServiceError(
                code="invalid_dates",
                message="End date cannot be before start date",
                status_code=400
            )

        # 2. Enforce overlap checks if active
        if new_active:
            overlaps = await BudgetRepository.get_active_overlapping_budgets(
                session=session,
                user_id=user_id,
                category=new_category,
                start_date=new_start,
                end_date=new_end,
                exclude_budget_id=b.id
            )
            if overlaps:
                raise FinanceServiceError(
                    code="budget_overlap",
                    message="An active budget already exists for this category during this period",
                    status_code=400
                )

        before_data = {
            "category": b.category,
            "limit_amount": float(b.limit_amount),
            "period": b.period,
            "start_date": str(b.start_date),
            "end_date": str(b.end_date) if b.end_date else None,
            "active": b.active
        }

        # Apply updates
        if payload.category is not None:
            b.category = payload.clean_category(payload.category)
        if payload.limit_amount is not None:
            b.limit_amount = payload.limit_amount
        if payload.period is not None:
            b.period = payload.period
        if payload.start_date is not None:
            b.start_date = payload.start_date
        if payload.end_date is not None:
            b.end_date = payload.end_date
        if payload.active is not None:
            b.active = payload.active

        b.updated_at = datetime.now(timezone.utc)

        after_data = {
            "category": b.category,
            "limit_amount": float(b.limit_amount),
            "period": b.period,
            "start_date": str(b.start_date),
            "end_date": str(b.end_date) if b.end_date else None,
            "active": b.active
        }

        await AuditLogRepository.create_audit_log(
            session=session,
            user_id=user_id,
            action="budget.updated",
            before=before_data,
            after=after_data
        )

        logger.info("Budget updated. user_id=%s, budget_id=%s", user_id, b.id)
        return b

    @staticmethod
    async def delete_budget(
        session: AsyncSession,
        user_id: str,
        budget_id: str
    ) -> None:
        """Delete an owned budget and record audit log."""
        b = await BudgetRepository.get_user_budget(session, user_id, budget_id)
        if not b:
            raise BudgetNotFoundError()

        before_data = {
            "id": b.id,
            "category": b.category,
            "limit_amount": float(b.limit_amount),
            "period": b.period,
            "start_date": str(b.start_date),
            "end_date": str(b.end_date) if b.end_date else None,
            "active": b.active
        }

        await BudgetRepository.delete_budget(session, budget_id)

        await AuditLogRepository.create_audit_log(
            session=session,
            user_id=user_id,
            action="budget.deleted",
            before=before_data,
            after=None
        )

        logger.info("Budget deleted. user_id=%s, budget_id=%s", user_id, budget_id)

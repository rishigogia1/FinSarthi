"""
services/recurring_cashflow_service.py — Business logic for recurring income/expense items.

Handles frequency validation, start/end bounds check, ownership validation, and audit tracking.
"""
import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.recurring_cashflow_repository import RecurringCashflowRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.models.recurring_cashflow import RecurringCashflow
from app.schemas.recurring_cashflow import CreateRecurringCashflowRequest, UpdateRecurringCashflowRequest
from app.services.transaction_service import FinanceServiceError

logger = logging.getLogger(__name__)


class RecurringCashflowNotFoundError(FinanceServiceError):
    def __init__(self):
        super().__init__("recurring_cashflow_not_found", "Recurring cashflow not found", status_code=404)


class RecurringCashflowService:
    @staticmethod
    async def create_cashflow(
        session: AsyncSession,
        user_id: str,
        payload: CreateRecurringCashflowRequest
    ) -> RecurringCashflow:
        """Create a recurring cashflow configuration and record audit log."""
        rc = await RecurringCashflowRepository.create_cashflow(
            session=session,
            user_id=user_id,
            type=payload.type,
            amount=payload.amount,
            category=payload.category,
            frequency=payload.frequency,
            start_date=payload.start_date,
            end_date=payload.end_date,
            note=payload.note,
            active=True
        )

        after_data = {
            "id": rc.id,
            "type": rc.type,
            "amount": float(rc.amount),
            "category": rc.category,
            "frequency": rc.frequency,
            "start_date": str(rc.start_date),
            "end_date": str(rc.end_date) if rc.end_date else None,
            "active": rc.active,
            "note": rc.note
        }

        await AuditLogRepository.create_audit_log(
            session=session,
            user_id=user_id,
            action="recurring_cashflow.created",
            before=None,
            after=after_data
        )

        logger.info("Recurring cashflow created. user_id=%s, cashflow_id=%s", user_id, rc.id)
        return rc

    @staticmethod
    async def list_cashflows(session: AsyncSession, user_id: str) -> list[RecurringCashflow]:
        """List recurring cashflows belonging to user."""
        return await RecurringCashflowRepository.list_user_cashflows(session, user_id)

    @staticmethod
    async def get_cashflow(
        session: AsyncSession,
        user_id: str,
        cashflow_id: str
    ) -> RecurringCashflow:
        """Fetch a specific recurring cashflow, enforcing ownership."""
        rc = await RecurringCashflowRepository.get_user_cashflow(session, user_id, cashflow_id)
        if not rc:
            raise RecurringCashflowNotFoundError()
        return rc

    @staticmethod
    async def update_cashflow(
        session: AsyncSession,
        user_id: str,
        cashflow_id: str,
        payload: UpdateRecurringCashflowRequest
    ) -> RecurringCashflow:
        """Update an owned recurring cashflow, validating dates and writing an audit trail."""
        rc = await RecurringCashflowRepository.get_user_cashflow(session, user_id, cashflow_id)
        if not rc:
            raise RecurringCashflowNotFoundError()

        # Date validation logic when partial properties are specified
        new_start = payload.start_date if payload.start_date is not None else rc.start_date
        new_end = payload.end_date if payload.end_date is not None else rc.end_date
        
        if new_end is not None and new_end < new_start:
            raise FinanceServiceError(
                code="invalid_dates",
                message="End date cannot be before start date",
                status_code=400
            )

        before_data = {
            "type": rc.type,
            "amount": float(rc.amount),
            "category": rc.category,
            "frequency": rc.frequency,
            "start_date": str(rc.start_date),
            "end_date": str(rc.end_date) if rc.end_date else None,
            "active": rc.active,
            "note": rc.note
        }

        # Apply updates
        if payload.type is not None:
            rc.type = payload.type
        if payload.amount is not None:
            rc.amount = payload.amount
        if payload.category is not None:
            rc.category = payload.clean_category(payload.category)
        if payload.frequency is not None:
            rc.frequency = payload.frequency
        if payload.start_date is not None:
            rc.start_date = payload.start_date
        if payload.end_date is not None:
            rc.end_date = payload.end_date
        if payload.active is not None:
            rc.active = payload.active
        if payload.note is not None:
            rc.note = payload.clean_note(payload.note)

        rc.updated_at = datetime.now(timezone.utc)

        after_data = {
            "type": rc.type,
            "amount": float(rc.amount),
            "category": rc.category,
            "frequency": rc.frequency,
            "start_date": str(rc.start_date),
            "end_date": str(rc.end_date) if rc.end_date else None,
            "active": rc.active,
            "note": rc.note
        }

        await AuditLogRepository.create_audit_log(
            session=session,
            user_id=user_id,
            action="recurring_cashflow.updated",
            before=before_data,
            after=after_data
        )

        logger.info("Recurring cashflow updated. user_id=%s, cashflow_id=%s", user_id, rc.id)
        return rc

    @staticmethod
    async def delete_cashflow(
        session: AsyncSession,
        user_id: str,
        cashflow_id: str
    ) -> None:
        """Delete an owned recurring cashflow and record audit trail."""
        rc = await RecurringCashflowRepository.get_user_cashflow(session, user_id, cashflow_id)
        if not rc:
            raise RecurringCashflowNotFoundError()

        before_data = {
            "id": rc.id,
            "type": rc.type,
            "amount": float(rc.amount),
            "category": rc.category,
            "frequency": rc.frequency,
            "start_date": str(rc.start_date),
            "end_date": str(rc.end_date) if rc.end_date else None,
            "active": rc.active,
            "note": rc.note
        }

        await RecurringCashflowRepository.delete_cashflow(session, cashflow_id)

        await AuditLogRepository.create_audit_log(
            session=session,
            user_id=user_id,
            action="recurring_cashflow.deleted",
            before=before_data,
            after=None
        )

        logger.info("Recurring cashflow deleted. user_id=%s, cashflow_id=%s", user_id, cashflow_id)

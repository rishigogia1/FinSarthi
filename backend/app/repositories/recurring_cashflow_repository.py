"""
repositories/recurring_cashflow_repository.py — Data access layer for RecurringCashflow model.
"""
from datetime import date
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.recurring_cashflow import RecurringCashflow


class RecurringCashflowRepository:
    @staticmethod
    async def get_user_cashflow(
        session: AsyncSession,
        user_id: str,
        cashflow_id: str
    ) -> RecurringCashflow | None:
        """Fetch a specific recurring cashflow entry owned by user."""
        stmt = select(RecurringCashflow).where(
            RecurringCashflow.id == cashflow_id,
            RecurringCashflow.user_id == user_id
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_user_cashflows(
        session: AsyncSession,
        user_id: str
    ) -> list[RecurringCashflow]:
        """List all recurring cashflow configurations belonging to a user."""
        stmt = select(RecurringCashflow).where(RecurringCashflow.user_id == user_id).order_by(RecurringCashflow.created_at.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create_cashflow(
        session: AsyncSession,
        user_id: str,
        type: str,
        amount: float,
        category: str,
        frequency: str,
        start_date: date,
        end_date: date | None = None,
        note: str | None = None,
        active: bool = True
    ) -> RecurringCashflow:
        """Create a new recurring cashflow configuration."""
        rc = RecurringCashflow(
            user_id=user_id,
            type=type,
            amount=amount,
            category=category,
            frequency=frequency,
            start_date=start_date,
            end_date=end_date,
            note=note,
            active=active
        )
        session.add(rc)
        await session.flush()
        return rc

    @staticmethod
    async def delete_cashflow(session: AsyncSession, cashflow_id: str) -> None:
        """Remove a recurring cashflow configuration from database."""
        stmt = delete(RecurringCashflow).where(RecurringCashflow.id == cashflow_id)
        await session.execute(stmt)

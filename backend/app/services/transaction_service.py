"""
services/transaction_service.py — Service layer for Transaction CRUD and lifecycle operations.
"""
import logging
import math
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.planner import TransactionCreateSchema
from app.schemas.transactions import UpdateTransactionRequest, TransactionQueryFilter, PaginatedTransactionsResponse, TransactionResponse
from app.services.dashboard_service import DashboardService

logger = logging.getLogger("app.services.transaction")


class TransactionServiceError(Exception):
    def __init__(self, message: str, status_code: int = 400, code: str = "bad_request"):
        self.message = message
        self.status_code = status_code
        self.code = code
        super().__init__(message)


FinanceServiceError = TransactionServiceError


class TransactionService:
    @classmethod
    def _invalidate_user_caches(cls, user_id: str) -> None:
        """Helper to clear dashboard and analytics caches when data mutates."""
        DashboardService.invalidate(user_id)
        from app.services.analytics_engine import AnalyticsEngine
        AnalyticsEngine.invalidate_cache(user_id)

    @classmethod
    async def create_transaction(
        cls,
        session: AsyncSession,
        user_id: str,
        payload: TransactionCreateSchema
    ) -> tuple[Transaction, bool]:
        """
        Creates a new transaction after validating data and checking idempotency.
        Returns tuple: (Transaction, is_duplicate: bool)
        """
        if payload.amount <= 0:
            raise TransactionServiceError("Amount must be greater than zero", status_code=422, code="invalid_amount")

        occurred_on = payload.occurred_on or date.today()

        # Idempotency guard window: 3s for manual UI entries (to handle accidental double-clicks), 60s for CHAT/automated sources
        window = 3 if (payload.source and payload.source.upper() == "MANUAL") else 60

        duplicate = await TransactionRepository.find_duplicate_transaction(
            session=session,
            user_id=user_id,
            type=payload.type,
            amount=payload.amount,
            category=payload.category,
            occurred_on=occurred_on,
            note=payload.note.strip() if payload.note else None,
            window_seconds=window
        )
        if duplicate:
            logger.info(
                "Duplicate transaction suppressed by idempotency guard: user_id=%s, type=%s, amount=%s, category=%s",
                user_id, payload.type, payload.amount, payload.category
            )
            return duplicate, True

        tx = await TransactionRepository.create_transaction(
            session=session,
            user_id=user_id,
            type=payload.type,
            amount=payload.amount,
            currency=payload.currency,
            category=payload.category,
            occurred_on=occurred_on,
            note=payload.note,
            source=getattr(payload, "source", "MANUAL")
        )

        logger.info(
            "Transaction Created: user_id=%s, type=%s, amount=%s, category=%s, source=%s, tx_id=%s",
            user_id, tx.type, tx.amount, tx.category, tx.source, tx.id
        )

        cls._invalidate_user_caches(user_id)
        return tx, False

    @classmethod
    async def get_transaction(
        cls,
        session: AsyncSession,
        user_id: str,
        transaction_id: str
    ) -> Transaction:
        """Retrieve an owned non-deleted transaction or raise 404."""
        tx = await TransactionRepository.get_user_transaction(session, user_id, transaction_id)
        if not tx:
            raise TransactionServiceError("Transaction not found", status_code=404, code="transaction_not_found")
        return tx

    @classmethod
    async def update_transaction(
        cls,
        session: AsyncSession,
        user_id: str,
        transaction_id: str,
        payload: UpdateTransactionRequest
    ) -> Transaction:
        """Update fields of an existing transaction."""
        tx = await TransactionRepository.get_user_transaction(session, user_id, transaction_id)
        if not tx:
            raise TransactionServiceError("Transaction not found", status_code=404, code="transaction_not_found")

        updates = payload.model_dump(exclude_unset=True)
        # Protect read-only source field
        updates.pop("source", None)

        updated_tx = await TransactionRepository.update_transaction(session, user_id, transaction_id, updates)
        if not updated_tx:
            raise TransactionServiceError("Transaction not found", status_code=404, code="transaction_not_found")

        logger.info("Transaction Updated: user_id=%s, tx_id=%s", user_id, transaction_id)
        cls._invalidate_user_caches(user_id)
        return updated_tx

    @classmethod
    async def delete_transaction(
        cls,
        session: AsyncSession,
        user_id: str,
        transaction_id: str
    ) -> bool:
        """Soft-delete an owned transaction."""
        deleted = await TransactionRepository.delete_transaction(session, user_id, transaction_id)
        if not deleted:
            raise TransactionServiceError("Transaction not found", status_code=404, code="transaction_not_found")

        logger.info("Transaction Soft-Deleted: user_id=%s, tx_id=%s", user_id, transaction_id)
        cls._invalidate_user_caches(user_id)
        return True

    @classmethod
    async def list_transactions(
        cls,
        session: AsyncSession,
        user_id: str,
        type: str | None = None,
        category: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int | None = None
    ) -> list[Transaction]:
        return await TransactionRepository.list_user_transactions(
            session=session,
            user_id=user_id,
            type=type,
            category=category,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )

    @classmethod
    async def list_transactions_paginated(
        cls,
        session: AsyncSession,
        user_id: str,
        filter_params: TransactionQueryFilter
    ) -> PaginatedTransactionsResponse:
        """Retrieve paginated transactions with total count and page metadata."""
        items = await TransactionRepository.list_user_transactions(session, user_id, filter_params=filter_params)
        total = await TransactionRepository.count_user_transactions(session, user_id, filter_params=filter_params)

        page_size = filter_params.page_size
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        return PaginatedTransactionsResponse(
            items=[TransactionResponse.model_validate(tx) for tx in items],
            total=total,
            page=filter_params.page,
            page_size=page_size,
            total_pages=total_pages
        )

    @classmethod
    async def create_expense(
        cls,
        session: AsyncSession,
        user_id: str,
        amount: float,
        category: str,
        occurred_on: date | None = None,
        note: str | None = None,
        source: str = "CHAT"
    ) -> tuple[Transaction, bool]:
        schema = TransactionCreateSchema(
            type="expense",
            amount=amount,
            category=category,
            occurred_on=occurred_on or date.today(),
            note=note,
            source=source
        )
        return await cls.create_transaction(session, user_id, schema)

    @classmethod
    async def create_income(
        cls,
        session: AsyncSession,
        user_id: str,
        amount: float,
        category: str,
        occurred_on: date | None = None,
        note: str | None = None,
        source: str = "CHAT"
    ) -> tuple[Transaction, bool]:
        schema = TransactionCreateSchema(
            type="income",
            amount=amount,
            category=category,
            occurred_on=occurred_on or date.today(),
            note=note,
            source=source
        )
        return await cls.create_transaction(session, user_id, schema)

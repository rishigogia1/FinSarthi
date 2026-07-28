"""
api/planner/routes.py — Router for Planner analytics and Transaction CRUD endpoints.
"""
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.planner import (
    TransactionCreateSchema,
    TransactionResponseSchema,
    PlannerSummaryResponseSchema,
)
from app.services.transaction_service import TransactionService, TransactionServiceError
from app.services.planner_analytics_service import PlannerAnalyticsService

router = APIRouter(prefix="", tags=["Planner & Transactions"])


# ---------------------------------------------------------------------------
# Transaction Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/transactions",
    response_model=TransactionResponseSchema,
    status_code=201
)
async def create_transaction(
    payload: TransactionCreateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TransactionResponseSchema:
    """Create a new transaction (expense or income) with validation and idempotency checks."""
    try:
        tx, _ = await TransactionService.create_transaction(db, current_user.id, payload)
        await db.commit()
        await db.refresh(tx)
        return TransactionResponseSchema.model_validate(tx)
    except TransactionServiceError as e:
        await db.rollback()
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": {"code": e.code, "message": e.message}}
        )


@router.get(
    "/transactions",
    response_model=list[TransactionResponseSchema]
)
async def list_transactions(
    type: str | None = Query(None, pattern="^(expense|income)$"),
    category: str | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    limit: int | None = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> list[TransactionResponseSchema]:
    """Retrieve filtered transaction history for current user."""
    txs = await TransactionService.list_transactions(
        session=db,
        user_id=current_user.id,
        type=type,
        category=category,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    return [TransactionResponseSchema.model_validate(tx) for tx in txs]


@router.delete(
    "/transactions/{transaction_id}",
    status_code=204
)
async def delete_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a user-owned transaction."""
    deleted = await TransactionService.delete_transaction(db, current_user.id, transaction_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found or not owned by current user"
        )
    await db.commit()


# ---------------------------------------------------------------------------
# Planner Summary Endpoint
# ---------------------------------------------------------------------------

@router.get(
    "/planner/summary",
    response_model=PlannerSummaryResponseSchema
)
async def get_planner_summary(
    year: int | None = Query(None),
    month: int | None = Query(None, ge=1, le=12),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PlannerSummaryResponseSchema:
    """Retrieve standardized Planner financial analytics summary computed from database records."""
    return await PlannerAnalyticsService.get_planner_summary(db, current_user.id, year, month)

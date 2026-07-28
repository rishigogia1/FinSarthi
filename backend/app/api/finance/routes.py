"""
api/finance/routes.py — Router for transactions, recurring cashflows, budgets, and summaries endpoints.

All routes require bearer JWT access token auth. Scoped by authenticated user id.
"""
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.transactions import (
    TransactionResponse,
    CreateTransactionRequest,
    UpdateTransactionRequest,
    TransactionQueryFilter,
    PaginatedTransactionsResponse
)
from app.schemas.recurring_cashflow import (
    RecurringCashflowResponse,
    CreateRecurringCashflowRequest,
    UpdateRecurringCashflowRequest
)
from app.schemas.budgets import (
    BudgetResponse,
    CreateBudgetRequest,
    UpdateBudgetRequest
)
from app.schemas.summaries import (
    OverviewSummaryResponse,
    CategoryBreakdownResponse,
    MonthlyCashflowPoint
)
from app.services.transaction_service import TransactionService, FinanceServiceError
from app.services.recurring_cashflow_service import RecurringCashflowService
from app.services.budget_service import BudgetService
from app.services.summary_service import SummaryService

router = APIRouter(prefix="/finance", tags=["Personal Finance Layer"])


def raise_http_exception(e: FinanceServiceError) -> None:
    """Helper translating core FinanceServiceError exceptions to FastAPI HTTPExceptions."""
    raise HTTPException(
        status_code=e.status_code,
        detail={
            "error": {
                "code": e.code,
                "message": e.message
            }
        }
    )


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------
@router.post(
    "/transactions",
    response_model=TransactionResponse,
    status_code=201
)
async def create_transaction(
    payload: CreateTransactionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TransactionResponse:
    """Create a manual transaction."""
    try:
        tx, _ = await TransactionService.create_transaction(db, current_user.id, payload)
        await db.commit()
    except FinanceServiceError as e:
        await db.rollback()
        raise_http_exception(e)
    return TransactionResponse.model_validate(tx)


@router.get(
    "/transactions",
    response_model=PaginatedTransactionsResponse | list[TransactionResponse]
)
async def list_transactions(
    type: str | None = Query(None, pattern="^(income|expense)$"),
    category: str | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    min_amount: float | None = Query(None, ge=0),
    max_amount: float | None = Query(None, ge=0),
    search: str | None = Query(None),
    sort_by: str = Query("occurred_on", pattern="^(occurred_on|amount|created_at|category)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int | None = Query(None, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    raw: bool = Query(False, description="Return raw array if True"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List owned transactions with optional search, filters, sorting, and pagination."""
    query_filter = TransactionQueryFilter(
        type=type,
        category=category,
        start_date=start_date,
        end_date=end_date,
        min_amount=min_amount,
        max_amount=max_amount,
        search=search,
        sort_by=sort_by,
        order=order,
        page=page or 1,
        page_size=page_size
    )

    if raw:
        txs = await TransactionService.list_transactions(
            session=db,
            user_id=current_user.id,
            type=type,
            category=category,
            start_date=start_date,
            end_date=end_date,
            limit=page_size
        )
        return [TransactionResponse.model_validate(tx) for tx in txs]

    return await TransactionService.list_transactions_paginated(db, current_user.id, query_filter)


@router.get(
    "/transactions/{transaction_id}",
    response_model=TransactionResponse
)
async def get_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TransactionResponse:
    """Retrieve an owned non-deleted transaction."""
    try:
        tx = await TransactionService.get_transaction(db, current_user.id, transaction_id)
    except FinanceServiceError as e:
        raise_http_exception(e)
    return TransactionResponse.model_validate(tx)


@router.patch(
    "/transactions/{transaction_id}",
    response_model=TransactionResponse
)
async def update_transaction(
    transaction_id: str,
    payload: UpdateTransactionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TransactionResponse:
    """Update an owned non-deleted transaction."""
    try:
        tx = await TransactionService.update_transaction(db, current_user.id, transaction_id, payload)
        await db.commit()
    except FinanceServiceError as e:
        await db.rollback()
        raise_http_exception(e)
    return TransactionResponse.model_validate(tx)


@router.delete(
    "/transactions/{transaction_id}",
    status_code=204
)
async def delete_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Soft-delete an owned transaction."""
    try:
        await TransactionService.delete_transaction(db, current_user.id, transaction_id)
        await db.commit()
    except FinanceServiceError as e:
        await db.rollback()
        raise_http_exception(e)


# ---------------------------------------------------------------------------
# Recurring Cashflows
# ---------------------------------------------------------------------------
@router.post(
    "/recurring",
    response_model=RecurringCashflowResponse,
    status_code=201
)
async def create_recurring_cashflow(
    payload: CreateRecurringCashflowRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> RecurringCashflowResponse:
    """Create a recurring flow template."""
    try:
        rc = await RecurringCashflowService.create_cashflow(db, current_user.id, payload)
        await db.commit()
    except FinanceServiceError as e:
        await db.rollback()
        raise_http_exception(e)
    return RecurringCashflowResponse.model_validate(rc)


@router.get(
    "/recurring",
    response_model=list[RecurringCashflowResponse]
)
async def list_recurring_cashflows(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> list[RecurringCashflowResponse]:
    """List all recurring flows config."""
    rcs = await RecurringCashflowService.list_cashflows(db, current_user.id)
    return [RecurringCashflowResponse.model_validate(rc) for rc in rcs]


@router.patch(
    "/recurring/{cashflow_id}",
    response_model=RecurringCashflowResponse
)
async def update_recurring_cashflow(
    cashflow_id: str,
    payload: UpdateRecurringCashflowRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> RecurringCashflowResponse:
    """Update an owned recurring flow."""
    try:
        rc = await RecurringCashflowService.update_cashflow(db, current_user.id, cashflow_id, payload)
        await db.commit()
    except FinanceServiceError as e:
        await db.rollback()
        raise_http_exception(e)
    return RecurringCashflowResponse.model_validate(rc)


@router.delete(
    "/recurring/{cashflow_id}",
    status_code=204
)
async def delete_recurring_cashflow(
    cashflow_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete an owned recurring flow."""
    try:
        await RecurringCashflowService.delete_cashflow(db, current_user.id, cashflow_id)
        await db.commit()
    except FinanceServiceError as e:
        await db.rollback()
        raise_http_exception(e)


# ---------------------------------------------------------------------------
# Budgets
# ---------------------------------------------------------------------------
@router.post(
    "/budgets",
    response_model=BudgetResponse,
    status_code=201
)
async def create_budget(
    payload: CreateBudgetRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> BudgetResponse:
    """Create a category budget."""
    try:
        b = await BudgetService.create_budget(db, current_user.id, payload)
        await db.commit()
    except FinanceServiceError as e:
        await db.rollback()
        raise_http_exception(e)
    return BudgetResponse.model_validate(b)


@router.get(
    "/budgets",
    response_model=list[BudgetResponse]
)
async def list_budgets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> list[BudgetResponse]:
    """List budgets belonging to user."""
    budgets = await BudgetService.list_budgets(db, current_user.id)
    return [BudgetResponse.model_validate(b) for b in budgets]


@router.patch(
    "/budgets/{budget_id}",
    response_model=BudgetResponse
)
async def update_budget(
    budget_id: str,
    payload: UpdateBudgetRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> BudgetResponse:
    """Update an owned budget."""
    try:
        b = await BudgetService.update_budget(db, current_user.id, budget_id, payload)
        await db.commit()
    except FinanceServiceError as e:
        await db.rollback()
        raise_http_exception(e)
    return BudgetResponse.model_validate(b)


@router.delete(
    "/budgets/{budget_id}",
    status_code=204
)
async def delete_budget(
    budget_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete an owned budget."""
    try:
        await BudgetService.delete_budget(db, current_user.id, budget_id)
        await db.commit()
    except FinanceServiceError as e:
        await db.rollback()
        raise_http_exception(e)


# ---------------------------------------------------------------------------
# Summaries
# ---------------------------------------------------------------------------
@router.get(
    "/summary/overview",
    response_model=OverviewSummaryResponse
)
async def get_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> OverviewSummaryResponse:
    """Get dynamic cashflow overview."""
    return await SummaryService.get_overview(db, current_user.id)


@router.get(
    "/summary/categories",
    response_model=list[CategoryBreakdownResponse]
)
async def get_category_breakdown(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> list[CategoryBreakdownResponse]:
    """Get transactions grouped by category allocations."""
    return await SummaryService.get_category_breakdown(db, current_user.id)


@router.get(
    "/summary/monthly-cashflow",
    response_model=list[MonthlyCashflowPoint]
)
async def get_monthly_cashflow(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> list[MonthlyCashflowPoint]:
    """Get chronological monthly cashflow points."""
    return await SummaryService.get_monthly_cashflow(db, current_user.id)

"""
repositories/transaction_repository.py — Data access layer for Transaction model.
"""
from datetime import date, datetime, timedelta, timezone
from sqlalchemy import select, func, and_, or_, cast, String
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.transaction import Transaction
from app.schemas.transactions import TransactionQueryFilter


class TransactionRepository:
    @staticmethod
    async def get_user_transaction(
        session: AsyncSession,
        user_id: str,
        transaction_id: str
    ) -> Transaction | None:
        """Fetch a specific non-deleted transaction owned by user."""
        stmt = select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id,
            Transaction.is_deleted == False
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def _build_query_conditions(user_id: str, filter_params: TransactionQueryFilter | None = None):
        conditions = [
            Transaction.user_id == user_id,
            Transaction.is_deleted == False
        ]
        if not filter_params:
            return conditions

        if filter_params.type:
            conditions.append(Transaction.type == filter_params.type)
        if filter_params.category:
            conditions.append(Transaction.category == filter_params.category)
        if filter_params.start_date:
            conditions.append(Transaction.occurred_on >= filter_params.start_date)
        if filter_params.end_date:
            conditions.append(Transaction.occurred_on <= filter_params.end_date)
        if filter_params.min_amount is not None:
            conditions.append(Transaction.amount >= filter_params.min_amount)
        if filter_params.max_amount is not None:
            conditions.append(Transaction.amount <= filter_params.max_amount)

        if filter_params.search:
            pattern = f"%{filter_params.search.strip()}%"
            conditions.append(
                or_(
                    Transaction.note.ilike(pattern),
                    Transaction.category.ilike(pattern),
                    Transaction.source.ilike(pattern),
                    cast(Transaction.amount, String).ilike(pattern)
                )
            )

        return conditions

    @staticmethod
    async def list_user_transactions(
        session: AsyncSession,
        user_id: str,
        filter_params: TransactionQueryFilter | None = None,
        type: str | None = None,
        category: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int | None = None
    ) -> list[Transaction]:
        """Query non-deleted transactions with search, filters, sorting, and pagination."""
        page_size = limit if limit else (filter_params.page_size if filter_params else 20)
        if filter_params is None:
            filter_params = TransactionQueryFilter(
                type=type,
                category=category,
                start_date=start_date,
                end_date=end_date,
                page_size=page_size
            )

        conditions = TransactionRepository._build_query_conditions(user_id, filter_params)
        stmt = select(Transaction).where(and_(*conditions))

        # Sorting
        sort_attr = getattr(Transaction, filter_params.sort_by, Transaction.occurred_on)
        if filter_params.order == "asc":
            stmt = stmt.order_by(sort_attr.asc(), Transaction.created_at.asc())
        else:
            stmt = stmt.order_by(sort_attr.desc(), Transaction.created_at.desc())

        # Pagination / Limit
        effective_limit = limit or filter_params.page_size
        offset = (filter_params.page - 1) * effective_limit
        stmt = stmt.offset(offset).limit(effective_limit)

        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def count_user_transactions(
        session: AsyncSession,
        user_id: str,
        filter_params: TransactionQueryFilter | None = None
    ) -> int:
        """Count total matching non-deleted transactions for pagination."""
        conditions = TransactionRepository._build_query_conditions(user_id, filter_params)
        stmt = select(func.count(Transaction.id)).where(and_(*conditions))
        result = await session.execute(stmt)
        return result.scalar() or 0

    @staticmethod
    async def create_transaction(
        session: AsyncSession,
        user_id: str,
        type: str,
        amount: float,
        currency: str,
        category: str,
        occurred_on: date,
        note: str | None = None,
        source: str = "MANUAL"
    ) -> Transaction:
        """Insert a transaction record."""
        now = datetime.now(timezone.utc)
        tx = Transaction(
            user_id=user_id,
            type=type,
            amount=amount,
            currency=currency,
            category=category,
            occurred_on=occurred_on,
            note=note,
            source=source,
            is_deleted=False,
            created_at=now,
            updated_at=now
        )
        session.add(tx)
        await session.flush()
        await session.refresh(tx)
        return tx

    @staticmethod
    async def update_transaction(
        session: AsyncSession,
        user_id: str,
        transaction_id: str,
        updates: dict
    ) -> Transaction | None:
        """Update an existing non-deleted transaction."""
        tx = await TransactionRepository.get_user_transaction(session, user_id, transaction_id)
        if not tx:
            return None

        for key, value in updates.items():
            if value is not None and hasattr(tx, key) and key not in ("id", "user_id", "created_at", "source"):
                setattr(tx, key, value)

        tx.updated_at = datetime.now(timezone.utc)
        await session.flush()
        return tx

    @staticmethod
    async def delete_transaction(session: AsyncSession, user_id: str, transaction_id: str) -> bool:
        """Soft-delete a user-owned transaction."""
        tx = await TransactionRepository.get_user_transaction(session, user_id, transaction_id)
        if not tx:
            return False

        tx.is_deleted = True
        tx.deleted_at = datetime.now(timezone.utc)
        await session.flush()
        return True

    @staticmethod
    async def find_duplicate_transaction(
        session: AsyncSession,
        user_id: str,
        type: str,
        amount: float,
        category: str,
        occurred_on: date,
        note: str | None = None,
        window_seconds: int = 60
    ) -> Transaction | None:
        """
        Idempotency check: Look for an identical transaction created within window_seconds.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
        stmt = select(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.type == type,
            Transaction.amount == amount,
            Transaction.category == category,
            Transaction.occurred_on == occurred_on,
            Transaction.created_at >= cutoff,
            Transaction.is_deleted == False
        )
        if note:
            stmt = stmt.where(Transaction.note == note)

        stmt = stmt.order_by(Transaction.created_at.desc()).limit(1)

        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_monthly_totals(
        session: AsyncSession,
        user_id: str,
        year: int,
        month: int
    ) -> dict[str, float]:
        """Aggregate total income and total expense for specified calendar month."""
        start_d = date(year, month, 1)
        if month == 12:
            end_d = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_d = date(year, month + 1, 1) - timedelta(days=1)

        stmt = select(
            Transaction.type,
            func.coalesce(func.sum(Transaction.amount), 0).label("total")
        ).where(
            Transaction.user_id == user_id,
            Transaction.occurred_on >= start_d,
            Transaction.occurred_on <= end_d,
            Transaction.is_deleted == False
        ).group_by(Transaction.type)

        result = await session.execute(stmt)
        rows = result.all()

        totals = {"expense": 0.0, "income": 0.0}
        for row in rows:
            totals[row.type] = float(row.total)

        return totals

    @staticmethod
    async def get_category_totals(
        session: AsyncSession,
        user_id: str,
        year: int,
        month: int,
        type: str = "expense"
    ) -> list[tuple[str, float]]:
        """Aggregate category totals for the specified month and type, sorted descending."""
        start_d = date(year, month, 1)
        if month == 12:
            end_d = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_d = date(year, month + 1, 1) - timedelta(days=1)

        stmt = select(
            Transaction.category,
            func.coalesce(func.sum(Transaction.amount), 0).label("total")
        ).where(
            Transaction.user_id == user_id,
            Transaction.type == type,
            Transaction.occurred_on >= start_d,
            Transaction.occurred_on <= end_d,
            Transaction.is_deleted == False
        ).group_by(Transaction.category).order_by(func.sum(Transaction.amount).desc())

        result = await session.execute(stmt)
        return [(str(row.category), float(row.total)) for row in result.all()]

    @staticmethod
    async def get_activity_metrics(
        session: AsyncSession,
        user_id: str,
        year: int,
        month: int
    ) -> dict:
        """Get total monthly count, count recorded today, and latest transaction details."""
        start_d = date(year, month, 1)
        if month == 12:
            end_d = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_d = date(year, month + 1, 1) - timedelta(days=1)

        today = date.today()

        count_stmt = select(func.count(Transaction.id)).where(
            Transaction.user_id == user_id,
            Transaction.occurred_on >= start_d,
            Transaction.occurred_on <= end_d,
            Transaction.is_deleted == False
        )
        count_res = await session.execute(count_stmt)
        total_count = count_res.scalar() or 0

        today_stmt = select(func.count(Transaction.id)).where(
            Transaction.user_id == user_id,
            Transaction.occurred_on == today,
            Transaction.is_deleted == False
        )
        today_res = await session.execute(today_stmt)
        today_count = today_res.scalar() or 0

        latest_stmt = select(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.is_deleted == False
        ).order_by(Transaction.occurred_on.desc(), Transaction.created_at.desc()).limit(1)
        latest_res = await session.execute(latest_stmt)
        latest = latest_res.scalar_one_or_none()

        return {
            "total_count": total_count,
            "today_count": today_count,
            "latest_category": latest.category if latest else None,
            "last_transaction_amount": float(latest.amount) if latest else None,
            "last_transaction_type": latest.type if latest else None,
        }

    @staticmethod
    async def get_daily_and_weekly_spend(
        session: AsyncSession,
        user_id: str,
        year: int,
        month: int
    ) -> dict[str, float]:
        """Calculate average daily expense for current month and current week total expense."""
        today = date.today()
        start_d = date(year, month, 1)
        if month == 12:
            end_d = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_d = date(year, month + 1, 1) - timedelta(days=1)

        monthly_totals = await TransactionRepository.get_monthly_totals(session, user_id, year, month)
        monthly_expense = monthly_totals["expense"]

        if today >= start_d and today <= end_d:
            days_count = max(1, today.day)
        else:
            days_count = max(1, (end_d - start_d).days + 1)

        avg_daily = monthly_expense / days_count

        week_start = today - timedelta(days=6)
        week_stmt = select(
            func.coalesce(func.sum(Transaction.amount), 0)
        ).where(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            Transaction.occurred_on >= week_start,
            Transaction.occurred_on <= today,
            Transaction.is_deleted == False
        )
        week_res = await session.execute(week_stmt)
        weekly_spend = float(week_res.scalar() or 0)

        return {
            "avg_daily_spend": round(avg_daily, 2),
            "weekly_spend": round(weekly_spend, 2)
        }

"""
services/analytics_engine.py — Core deterministic financial analytics service with caching.

Single source of truth for transaction calculations consumed by Planner, Coach, and future agents.
"""
import time
import logging
from datetime import date, timedelta
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.transaction_repository import TransactionRepository
from app.core.coach_config import coach_settings

logger = logging.getLogger("app.services.analytics_engine")


class AnalyticsCache:
    """Simple in-memory TTL cache for user analytics snapshots."""
    def __init__(self, ttl_seconds: int = 30):
        self._cache: dict[str, tuple[float, Any]] = {}
        self.ttl_seconds = ttl_seconds

    def get(self, key: str) -> Any | None:
        if key in self._cache:
            ts, value = self._cache[key]
            if time.time() - ts < self.ttl_seconds:
                return value
            else:
                del self._cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        self._cache[key] = (time.time(), value)

    def invalidate_user(self, user_id: str) -> None:
        prefix = f"{user_id}:"
        keys_to_del = [k for k in self._cache.keys() if k.startswith(prefix)]
        for k in keys_to_del:
            del self._cache[k]


_analytics_cache = AnalyticsCache(ttl_seconds=coach_settings.ANALYTICS_CACHE_TTL_SECONDS)


class AnalyticsEngine:
    @classmethod
    def invalidate_cache(cls, user_id: str) -> None:
        """Invalidates all cached analytics snapshots for a given user."""
        _analytics_cache.invalidate_user(user_id)
        logger.debug("Analytics cache invalidated for user=%s", user_id)

    @classmethod
    async def get_financial_summary(
        cls,
        session: AsyncSession,
        user_id: str,
        year: int | None = None,
        month: int | None = None
    ) -> dict[str, Any]:
        """
        Calculates and returns a complete financial summary dictionary.
        Utilizes a 30s TTL cache to avoid redundant SQL queries across Planner & Coach.
        """
        today = date.today()
        year = year or today.year
        month = month or today.month
        cache_key = f"{user_id}:{year}:{month}"

        cached = _analytics_cache.get(cache_key)
        if cached is not None:
            logger.debug("Analytics cache hit for user=%s (%02d/%d)", user_id, month, year)
            return cached

        # 1. Monthly Totals
        totals = await TransactionRepository.get_monthly_totals(session, user_id, year, month)
        monthly_expense = totals["expense"]
        monthly_income = totals["income"]
        net_cashflow = monthly_income - monthly_expense
        savings_rate = round((net_cashflow / monthly_income * 100), 1) if monthly_income > 0 else 0.0

        # 2. Category Breakdown
        cat_rows = await TransactionRepository.get_category_totals(session, user_id, year, month, type="expense")
        categories = []
        largest_cat = None
        largest_cat_amount = 0.0

        if cat_rows:
            largest_cat = cat_rows[0][0]
            largest_cat_amount = cat_rows[0][1]

        for cat_name, cat_amount in cat_rows:
            pct = round((cat_amount / monthly_expense * 100), 1) if monthly_expense > 0 else 0.0
            categories.append({
                "category": cat_name,
                "total_amount": cat_amount,
                "percentage": pct
            })

        # Most Frequent Category
        tx_list = await TransactionRepository.list_user_transactions(session, user_id, limit=500)
        category_counts: dict[str, int] = {}
        for tx in tx_list:
            if tx.type == "expense":
                category_counts[tx.category] = category_counts.get(tx.category, 0) + 1
        most_frequent_cat = max(category_counts.items(), key=lambda x: x[1])[0] if category_counts else None

        # 3. Activity Metrics
        act_raw = await TransactionRepository.get_activity_metrics(session, user_id, year, month)
        total_transactions = act_raw["total_count"]
        today_count = act_raw["today_count"]
        latest_category = act_raw["latest_category"]
        last_transaction_amount = act_raw["last_transaction_amount"]
        last_transaction_type = act_raw["last_transaction_type"]

        # 4. Daily & Weekly Spend
        spend_raw = await TransactionRepository.get_daily_and_weekly_spend(session, user_id, year, month)
        avg_daily_spend = spend_raw["avg_daily_spend"]
        weekly_spend = spend_raw["weekly_spend"]

        # 5. History / Readiness Days Calculation
        first_tx_date = None
        total_all_tx_count = len(tx_list)
        if tx_list:
            sorted_txs = sorted(tx_list, key=lambda t: t.occurred_on)
            first_tx_date = sorted_txs[0].occurred_on
            days_history = max(1, (today - first_tx_date).days + 1)
        else:
            days_history = 0

        # Spending frequency
        days_in_period = max(1, today.day if (today.year == year and today.month == month) else 30)
        avg_tx_per_day = round(total_transactions / days_in_period, 2)

        # Spending consistency (highest/lowest spend days in current month)
        daily_expense_map: dict[date, float] = {}
        for tx in tx_list:
            if tx.type == "expense" and tx.occurred_on.year == year and tx.occurred_on.month == month:
                daily_expense_map[tx.occurred_on] = daily_expense_map.get(tx.occurred_on, 0.0) + float(tx.amount)

        highest_spend_day = None
        lowest_spend_day = None
        if daily_expense_map:
            max_d, max_amt = max(daily_expense_map.items(), key=lambda x: x[1])
            min_d, min_amt = min(daily_expense_map.items(), key=lambda x: x[1])
            highest_spend_day = {"date": str(max_d), "day_name": max_d.strftime("%A"), "amount": round(max_amt, 2)}
            lowest_spend_day = {"date": str(min_d), "day_name": min_d.strftime("%A"), "amount": round(min_amt, 2)}

        summary = {
            "year": year,
            "month": month,
            "overview": {
                "monthly_expense": monthly_expense,
                "monthly_income": monthly_income,
                "net_cashflow": net_cashflow,
                "savings_rate": savings_rate
            },
            "categories": categories,
            "activity": {
                "total_transactions": total_transactions,
                "today_count": today_count,
                "latest_category": latest_category,
                "last_transaction_amount": last_transaction_amount,
                "last_transaction_type": last_transaction_type
            },
            "analytics": {
                "avg_daily_spend": avg_daily_spend,
                "weekly_spend": weekly_spend,
                "largest_category": largest_cat,
                "largest_category_amount": largest_cat_amount,
                "most_frequent_category": most_frequent_cat,
                "total_transactions": total_transactions,
                "total_all_transactions": total_all_tx_count,
                "avg_tx_per_day": avg_tx_per_day
            },
            "consistency": {
                "highest_spend_day": highest_spend_day,
                "lowest_spend_day": lowest_spend_day
            },
            "history": {
                "total_tx_count": total_all_tx_count,
                "days_history": days_history,
                "first_tx_date": str(first_tx_date) if first_tx_date else None
            }
        }

        _analytics_cache.set(cache_key, summary)
        logger.debug("Analytics computed and cached for user=%s (%02d/%d)", user_id, month, year)
        return summary

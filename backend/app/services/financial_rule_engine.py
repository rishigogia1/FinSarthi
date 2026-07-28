"""
services/financial_rule_engine.py — Generic multi-agent rule engine evaluating financial rules.

Extensible framework for evaluating financial rules across Coach, Planner, Guardian, and Navigator.
"""
import logging
from abc import ABC, abstractmethod
from typing import Any

from app.schemas.rule_result import RuleResult
from app.core.coach_config import coach_settings

logger = logging.getLogger("app.services.financial_rule_engine")


class BaseRule(ABC):
    rule_id: str
    title: str

    @abstractmethod
    def evaluate(self, analytics: dict[str, Any]) -> RuleResult | None:
        """Evaluate rule against analytics snapshot dictionary. Return RuleResult or None."""
        pass


class FoodOverspendRule(BaseRule):
    rule_id = "food_overspend"
    title = "Food & Dining Spend"

    def evaluate(self, analytics: dict[str, Any]) -> RuleResult | None:
        categories = analytics.get("categories", [])
        food_cat = next((c for c in categories if c["category"].lower() == "food"), None)

        if food_cat and food_cat["percentage"] > coach_settings.FOOD_OVERSPEND_PCT:
            pct = food_cat["percentage"]
            amt = food_cat["total_amount"]
            return RuleResult(
                rule_id=self.rule_id,
                title=self.title,
                severity="medium",
                explanation=f"Food accounts for {pct:.1f}% of your monthly expenses (₹{amt:,.2f}).",
                recommendation="Food spending is above target. Consider cooking at home twice a week to lower expenses.",
                metrics={"food_percentage": pct, "food_amount": amt}
            )
        return None


class ShoppingOverspendRule(BaseRule):
    rule_id = "shopping_overspend"
    title = "Shopping Spend"

    def evaluate(self, analytics: dict[str, Any]) -> RuleResult | None:
        categories = analytics.get("categories", [])
        shopping_cat = next((c for c in categories if c["category"].lower() == "shopping"), None)

        if shopping_cat and shopping_cat["percentage"] > coach_settings.SHOPPING_OVERSPEND_PCT:
            pct = shopping_cat["percentage"]
            amt = shopping_cat["total_amount"]
            return RuleResult(
                rule_id=self.rule_id,
                title=self.title,
                severity="medium",
                explanation=f"Shopping accounts for {pct:.1f}% of your monthly expenses (₹{amt:,.2f}).",
                recommendation="Shopping is a major expense category. Consider delaying non-essential purchases for one week.",
                metrics={"shopping_percentage": pct, "shopping_amount": amt}
            )
        return None


class NegativeCashflowRule(BaseRule):
    rule_id = "negative_cashflow"
    title = "Cashflow Deficit"

    def evaluate(self, analytics: dict[str, Any]) -> RuleResult | None:
        overview = analytics.get("overview", {})
        monthly_expense = overview.get("monthly_expense", 0.0)
        monthly_income = overview.get("monthly_income", 0.0)

        if monthly_expense > monthly_income and monthly_income > 0:
            diff = monthly_expense - monthly_income
            return RuleResult(
                rule_id=self.rule_id,
                title=self.title,
                severity="high",
                explanation=f"Your expenses (₹{monthly_expense:,.2f}) exceed your monthly income (₹{monthly_income:,.2f}) by ₹{diff:,.2f}.",
                recommendation="Review recurring expenses before making new purchases to bring cashflow back into positive territory.",
                metrics={"monthly_expense": monthly_expense, "monthly_income": monthly_income, "deficit": diff}
            )
        return None


class LowSavingsRule(BaseRule):
    rule_id = "low_savings"
    title = "Savings Rate Warning"

    def evaluate(self, analytics: dict[str, Any]) -> RuleResult | None:
        overview = analytics.get("overview", {})
        savings_rate = overview.get("savings_rate", 0.0)
        monthly_income = overview.get("monthly_income", 0.0)
        monthly_expense = overview.get("monthly_expense", 0.0)

        if monthly_income > 0 and monthly_expense <= monthly_income and savings_rate < coach_settings.LOW_SAVINGS_PCT:
            return RuleResult(
                rule_id=self.rule_id,
                title=self.title,
                severity="medium",
                explanation=f"Your savings rate is currently {savings_rate:.1f}%, which is below the 20% target.",
                recommendation="Try setting aside 10% of your income first on payday before planning discretionary spending.",
                metrics={"savings_rate": savings_rate}
            )
        return None


class HighSavingsRule(BaseRule):
    rule_id = "high_savings"
    title = "Strong Savings Rate"

    def evaluate(self, analytics: dict[str, Any]) -> RuleResult | None:
        overview = analytics.get("overview", {})
        savings_rate = overview.get("savings_rate", 0.0)
        monthly_income = overview.get("monthly_income", 0.0)

        if monthly_income > 0 and savings_rate >= coach_settings.HIGH_SAVINGS_PCT:
            return RuleResult(
                rule_id=self.rule_id,
                title=self.title,
                severity="info",
                explanation=f"Excellent work! Your savings rate is strong at {savings_rate:.1f}%.",
                recommendation="Maintain your current budget disciplines and explore allocating extra savings toward long-term goals.",
                metrics={"savings_rate": savings_rate}
            )
        return None


class FinancialRuleEngine:
    _rules: list[BaseRule] = [
        FoodOverspendRule(),
        ShoppingOverspendRule(),
        NegativeCashflowRule(),
        LowSavingsRule(),
        HighSavingsRule()
    ]

    @classmethod
    def evaluate_rules(cls, analytics: dict[str, Any]) -> list[RuleResult]:
        """Runs all registered rules against the financial analytics dictionary."""
        results: list[RuleResult] = []
        for rule in cls._rules:
            try:
                res = rule.evaluate(analytics)
                if res:
                    results.append(res)
            except Exception as e:
                logger.error("Error evaluating rule %s: %s", rule.rule_id, e)
        return results

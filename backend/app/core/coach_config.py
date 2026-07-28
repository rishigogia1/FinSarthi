"""
core/coach_config.py — Centralized configuration settings for Coach agent & rule thresholds.
"""

class CoachSettings:
    # Readiness thresholds
    MIN_TRANSACTIONS: int = 20
    MIN_HISTORY_DAYS: int = 30

    # Rule evaluation thresholds
    FOOD_OVERSPEND_PCT: float = 40.0       # Trigger if Food > 40% of expense
    SHOPPING_OVERSPEND_PCT: float = 25.0   # Trigger if Shopping > 25% of expense
    LOW_SAVINGS_PCT: float = 20.0          # Trigger if Savings rate < 20%
    HIGH_SAVINGS_PCT: float = 30.0         # Trigger praise if Savings rate >= 30%

    # Cache TTL for Analytics Engine (seconds)
    ANALYTICS_CACHE_TTL_SECONDS: int = 30


coach_settings = CoachSettings()

"""
schemas/rule_result.py — Standardized data structure for financial rule evaluation outputs.
"""
from typing import Any, Literal
from pydantic import BaseModel, Field


class RuleResult(BaseModel):
    rule_id: str = Field(..., description="Unique key identifying the rule (e.g. food_overspend)")
    title: str = Field(..., description="Short descriptive title of the rule finding")
    severity: Literal["info", "low", "medium", "high"] = Field("info", description="Severity or importance rating")
    explanation: str = Field(..., description="Deterministic findings explaining why rule was triggered")
    recommendation: str = Field(..., description="Actionable recommendation or coaching tip")
    metrics: dict[str, Any] = Field(default_factory=dict, description="Contextual metric key-values")

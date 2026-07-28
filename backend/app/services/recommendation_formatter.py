"""
services/recommendation_formatter.py — LLM natural language explanation layer.

Converts structured RuleResults & summary metrics into friendly natural language text.
"""
import json
import logging
from typing import Any

from app.schemas.rule_result import RuleResult
from app.services.llm_service import LLMService, LLMError

logger = logging.getLogger("app.services.recommendation_formatter")


class RecommendationFormatter:
    @classmethod
    async def format_coaching(
        cls,
        status: str,
        score: int | None,
        savings_rate: float,
        largest_category: str | None,
        recommendations: list[RuleResult],
        tx_count: int,
        required_tx: int
    ) -> str:
        """
        Generates friendly natural language coaching text.
        If status is 'Learning', returns an encouraging progress explanation.
        If status is 'Active', sends compact JSON context to LLM for rephrasing.
        """
        if status == "Learning":
            needed = max(1, required_tx - tx_count)
            return (
                f"I'm currently observing your financial habits. "
                f"You've recorded {tx_count} transaction(s) so far. "
                f"Once you reach {required_tx} transactions (or 30 days of history), "
                f"I'll generate your personalized Coach Score and deep habit analysis."
            )

        # Build compact payload for LLM
        compact_context = {
            "coach_score": score,
            "savings_rate_pct": savings_rate,
            "largest_category": largest_category or "None",
            "findings": [
                {
                    "title": r.title,
                    "explanation": r.explanation,
                    "recommendation": r.recommendation
                }
                for r in recommendations
            ]
        }

        system_prompt = (
            "You are FinSarthi Coach, a friendly and empathetic financial behavioral coach.\n"
            "Rewrite the structured financial summary into a concise, natural, encouraging coaching response (2-3 sentences max).\n"
            "STRICT RULES:\n"
            "1. NEVER alter, change, or estimate any numbers, percentages, or figures provided in the context.\n"
            "2. NEVER invent financial facts, metrics, or transactions.\n"
            "3. Focus on practical spending habits and actionable advice.\n"
            "4. Keep the tone warm, clear, and supportive."
        )

        user_content = json.dumps(compact_context, indent=2)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Structured Context:\n{user_content}"}
        ]

        try:
            res = await LLMService.generate(messages=messages, temperature=0.5, max_tokens=250, timeout=5.0)
            return res["content"].strip()
        except LLMError as e:
            logger.warning("LLM formatting failed: %s. Using deterministic fallback.", e)
            return cls._deterministic_fallback(score, savings_rate, largest_category, recommendations)
        except Exception as e:
            logger.exception("Unexpected error in RecommendationFormatter: %s", e)
            return cls._deterministic_fallback(score, savings_rate, largest_category, recommendations)

    @classmethod
    def _deterministic_fallback(
        cls,
        score: int | None,
        savings_rate: float,
        largest_category: str | None,
        recommendations: list[RuleResult]
    ) -> str:
        parts = []
        if score is not None:
            parts.append(f"Your Coach Score is **{score}/100**.")
        if largest_category:
            parts.append(f"Your largest spending category this month is **{largest_category}**.")
        if savings_rate > 0:
            parts.append(f"Your current savings rate is **{savings_rate:.1f}%**.")

        if recommendations:
            top_rec = recommendations[0]
            parts.append(f"💡 Recommendation: {top_rec.recommendation}")
        else:
            parts.append("Keep up your steady financial habits!")

        return " ".join(parts)

"""
services/ai_explanation_service.py — AI-generated explanations of computed metrics.

Communicates with the active LLM provider via httpx, falling back gracefully to static templates if offline.
"""
import logging
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.schemas.insights import InsightResponse

logger = logging.getLogger(__name__)


class AIExplanationService:
    @staticmethod
    def get_fallback_explanation(insight: InsightResponse) -> str:
        """Provide a clean structured template explanation when the LLM is unreachable."""
        evidence = insight.evidence or {}
        
        if insight.type == "budget_alert":
            cat = evidence.get("category", "selected category")
            act = evidence.get("actual", 0.0)
            lim = evidence.get("limit", 0.0)
            return f"Your monthly spending on {cat} has reached INR {round(act, 2)}, exceeding your budget of INR {round(lim, 2)}. Consider reducing discretionary purchases in this category."
            
        if insight.type == "goal_warning":
            return f"Your savings pace is currently below the required target rate. Adjusting your target date or increasing allocations can help you achieve this goal."
            
        if insight.type == "savings_insight":
            rate = evidence.get("savings_rate", 0.0)
            return f"Your overall savings rate of {round(rate, 2)}% is a strong financial signal. Consistent saving habits build long-term capital security."
            
        if insight.type == "low_history":
            return "Projections and insights will become more personalized as you log more transactions over time."
            
        return insight.message

    @staticmethod
    async def generate_explanation(
        session: AsyncSession,
        user_id: str,
        insight: InsightResponse
    ) -> str:
        """Call the active LLM provider to format insight prose, falling back to templates on errors."""
        evidence = insight.evidence or {}
        
        # Grounding context prompt
        system_instructions = (
            "You are a helpful personal finance assistant. Explain the following structured insight to the user. "
            "Follow these rules strictly:\n"
            "1. Ground your explanation ONLY in the provided evidence metrics. Do not invent any numbers.\n"
            "2. Wording must be concise, informational, and non-alarmist.\n"
            "3. Do NOT provide absolute investment or fiduciary advice. Use general educational phrasing.\n"
            "4. Keep the output under 3 sentences and do not include markdown headers or bullet points."
        )
        
        user_prompt = f"Insight Title: {insight.title}\nInsight Context: {insight.message}\nEvidence: {evidence}"
        
        provider = settings.LLM_PROVIDER
        try:
            from app.services.llm_service import LLMService, LLMError
            
            messages = [
                {"role": "system", "content": system_instructions},
                {"role": "user", "content": user_prompt}
            ]
            
            result = await LLMService.generate(
                messages=messages,
                temperature=0.2,
                max_tokens=150,
                timeout=4.0
            )
            return result["content"]
                    
        except Exception as e:
            logger.warning("LLM explanation call failed, falling back to static templates. Error: %s", e)
            
        # Graceful degradation fallback
        return AIExplanationService.get_fallback_explanation(insight)

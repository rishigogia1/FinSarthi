"""
services/response_validator.py — Agent Response Validator for FinSarthi V2.

Ensures agent outputs comply with persona boundaries, prevents template leakage,
and validates that specialized workflows do not return generic Copilot guidance headers.
"""
import logging
from typing import Tuple

logger = logging.getLogger("app.services.response_validator")


class ResponseValidator:
    @classmethod
    def validate(cls, content: str, target_agent: str) -> Tuple[bool, str]:
        """
        Validates LLM / agent output content against target_agent rules.

        Returns:
            Tuple of (is_valid, sanitized_or_fallback_content)
        """
        if not content or not content.strip():
            logger.warning("ResponseValidator: Empty content for target_agent=%s", target_agent)
            return (False, "I apologize, but I couldn't generate a complete response. Please try asking again.")

        agent_clean = (target_agent or "Copilot").capitalize()

        # Rule: Specialized agents MUST NOT leak generic Copilot card headers
        if agent_clean in ["Learn", "Guardian", "Navigator", "Coach", "Planner"]:
            if "✨ FinSarthi Copilot Guidance" in content or "✨ **FinSarthi Copilot Guidance**" in content:
                logger.warning(
                    "ResponseValidator: Detected generic Copilot header leakage in specialized agent %s",
                    agent_clean
                )
                return (False, f"[{agent_clean}] I am focused on your {agent_clean} inquiry. Let's continue.")

        return (True, content)

from abc import ABC, abstractmethod
from app.schemas.dashboard import AgentDashboardResponse
from app.schemas.dashboard_context import AgentContext
from datetime import datetime

class BaseAgent(ABC):
    """
    Abstract base class for all Dashboard AI Agents.
    Forces all agents to implement generate().
    """
    
    @abstractmethod
    async def generate(self, context: AgentContext) -> AgentDashboardResponse:
        """
        Generates the dashboard response for this specific agent.
        Must return AgentDashboardResponse.
        """
        pass
        
    def _create_fallback_response(self, id: str, name: str, role: str, desc: str) -> AgentDashboardResponse:
        """Helper to create a fallback response when data is missing or error occurs."""
        return AgentDashboardResponse(
            id=id,
            name=name,
            role=role,
            description=desc,
            implementation_status="Unavailable",
            current_phase="Unknown",
            requirements=[],
            metrics={},
            recommendations=[],
            activities=["Error loading agent data."],
            actions=[],
            last_updated=datetime.utcnow()
        )

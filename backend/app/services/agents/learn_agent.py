from datetime import datetime
from app.services.agents.base_agent import BaseAgent
from app.services.agents.registry import AgentRegistry
from app.schemas.dashboard import AgentDashboardResponse
from app.schemas.dashboard_context import AgentContext

class LearnAgent(BaseAgent):
    async def generate(self, context: AgentContext) -> AgentDashboardResponse:
        agent_id = "learn"
        name = "Learn"
        role = "Financial Literacy"
        desc = "Explains concepts simply, in your language."
        
        return AgentDashboardResponse(
            id=agent_id,
            name=name,
            role=role,
            description=desc,
            implementation_status="Available",
            current_phase="V1",
            requirements=[],
            metrics={},
            recommendations=[],
            activities=[
                "What is SIP?",
                "Explain Mutual Funds",
                "Credit Score",
                "Emergency Fund"
            ],
            actions=[{"label": "Explore Topics", "href": "/app/knowledge"}],
            last_updated=datetime.utcnow()
        )

AgentRegistry.register(LearnAgent)

from datetime import datetime
from app.services.agents.base_agent import BaseAgent
from app.services.agents.registry import AgentRegistry
from app.schemas.dashboard import AgentDashboardResponse
from app.schemas.dashboard_context import AgentContext

class GuardianAgent(BaseAgent):
    async def generate(self, context: AgentContext) -> AgentDashboardResponse:
        agent_id = "guardian"
        name = "Guardian"
        role = "Fraud & Safety"
        desc = "Watches for scams, suspicious links, and risky requests."
        
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
                "Verify suspicious links",
                "Check UPI requests",
                "Explain fraud attempts",
                "Provide online safety guidance"
            ],
            actions=[{"label": "Chat with Guardian", "href": "/app/chat"}],
            last_updated=datetime.utcnow()
        )

AgentRegistry.register(GuardianAgent)

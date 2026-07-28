from datetime import datetime
from app.services.agents.base_agent import BaseAgent
from app.services.agents.registry import AgentRegistry
from app.schemas.dashboard import AgentDashboardResponse
from app.schemas.dashboard_context import AgentContext

class NavigatorAgent(BaseAgent):
    async def generate(self, context: AgentContext) -> AgentDashboardResponse:
        agent_id = "navigator"
        name = "Navigator"
        role = "Schemes & Benefits"
        desc = "Navigator recommends government schemes, benefits, and tax opportunities after profile information is completed."
        
        profile = context.profile or {}
        
        requirements = [
            {"name": "Income details", "met": bool(profile.get("income"))},
            {"name": "Occupation details", "met": bool(profile.get("occupation"))},
            {"name": "Location details", "met": bool(profile.get("location"))},
        ]
        
        return AgentDashboardResponse(
            id=agent_id,
            name=name,
            role=role,
            description=desc,
            implementation_status="Waiting",
            current_phase="V2",
            requirements=requirements,
            metrics={},
            recommendations=[],
            activities=[],
            actions=[],
            last_updated=datetime.utcnow()
        )

AgentRegistry.register(NavigatorAgent)

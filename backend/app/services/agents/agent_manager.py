import asyncio
import logging
import time
from app.schemas.dashboard import AgentDashboardResponse
from app.schemas.dashboard_context import AgentContext
from app.services.agents.registry import AgentRegistry
from app.services.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

class AgentManager:
    """
    Executes registered agents in parallel and gathers their responses.
    Handles observability and individual agent failures.
    """

    @classmethod
    async def load_all(cls, context: AgentContext) -> list[AgentDashboardResponse]:
        agents = AgentRegistry.get_all_agents()
        if not agents:
            logger.warning("AgentManager loaded but no agents are registered in AgentRegistry!")
            return []

        # Run all agents in parallel
        tasks = [cls._safe_generate(agent, context) for agent in agents]
        results = await asyncio.gather(*tasks)
        
        return list(results)

    @classmethod
    async def _safe_generate(cls, agent: BaseAgent, context: AgentContext) -> AgentDashboardResponse:
        agent_name = agent.__class__.__name__
        start_time = time.perf_counter()
        logger.info(f"Loading {agent_name}...")
        
        try:
            # We assume all agents return an AgentDashboardResponse
            response = await agent.generate(context)
            elapsed = (time.perf_counter() - start_time) * 1000
            logger.info(f"{agent_name} complete in {elapsed:.2f}ms")
            return response
            
        except Exception as e:
            elapsed = (time.perf_counter() - start_time) * 1000
            logger.error(f"{agent_name} failed after {elapsed:.2f}ms. Error: {e}", exc_info=True)
            # Create a generic fallback if generation fails
            # We don't have the exact ID/Role here easily since that's inside the agent's logic usually,
            # but we can try to guess or use generic values
            return AgentDashboardResponse(
                id=agent_name.lower().replace("agent", ""),
                name=agent_name.replace("Agent", ""),
                role="Unknown",
                description="This agent encountered an error.",
                implementation_status="Unavailable",
                current_phase="Unknown",
                requirements=[],
                metrics={},
                recommendations=[],
                activities=["Error loading agent data."],
                actions=[],
                last_updated=context.user.created_at # fallback
            )

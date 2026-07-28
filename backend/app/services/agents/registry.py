import logging
from typing import Type
from app.services.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

class AgentRegistry:
    """
    Maintains a list of registered agents to load dynamically.
    Adding a new agent is simply calling AgentRegistry.register(NewAgent).
    """
    _agents: list[Type[BaseAgent]] = []

    @classmethod
    def register(cls, agent_class: Type[BaseAgent]):
        if agent_class not in cls._agents:
            cls._agents.append(agent_class)
            logger.info("Registered agent: %s", agent_class.__name__)

    @classmethod
    def get_all_agents(cls) -> list[BaseAgent]:
        return [agent_class() for agent_class in cls._agents]

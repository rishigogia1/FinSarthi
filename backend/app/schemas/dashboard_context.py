from typing import Any
from pydantic import BaseModel, ConfigDict
from app.models.user import User

class AgentContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    user: User
    session: Any | None = None
    planner_summary: Any | None = None
    profile: dict[str, Any] | None = None
    budgets: list[Any] = []
    goals: list[Any] = []
    transactions: list[Any] = []
    coach_summary: Any | None = None
    conversation_history: list[dict[str, str]] = []
    topic_memory: dict[str, Any] = {}
    preferences: dict[str, Any] | None = None
    analytics: dict[str, Any] = {}
    
    # Workflow runtime state
    workflow_id: str | None = None
    workflow_status: str = "ACTIVE"
    primary_agent: str | None = None
    supporting_agents: list[str] = []
    workflow_state: dict[str, Any] = {}
    workflow_memory: dict[str, Any] = {}

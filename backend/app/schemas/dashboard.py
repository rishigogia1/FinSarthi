from datetime import datetime
from typing import Any
from pydantic import BaseModel

class AgentDashboardResponse(BaseModel):
    id: str
    name: str
    role: str
    description: str
    implementation_status: str
    current_phase: str
    requirements: list[dict[str, Any]]
    metrics: dict[str, Any]
    recommendations: list[str]
    activities: list[str]
    actions: list[dict[str, str]]
    last_updated: datetime

class TeamDashboardResponse(BaseModel):
    request_id: str
    total_time_ms: float
    agents: list[AgentDashboardResponse]

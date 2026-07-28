import uuid
import time
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Tuple

from app.models.user import User
from app.repositories.dashboard_repository import DashboardRepository
from app.services.agents.agent_manager import AgentManager
# Import the agents package to trigger registrations
import app.services.agents

from app.schemas.dashboard import TeamDashboardResponse

logger = logging.getLogger(__name__)

class DashboardService:
    # A simple in-memory cache for Phase 1: { user_id: (TeamDashboardResponse, timestamp) }
    _cache: Dict[str, Tuple[TeamDashboardResponse, float]] = {}
    CACHE_TTL_SECONDS = 300 # 5 minutes
    
    @classmethod
    async def get_team_dashboard(cls, session: AsyncSession, user: User) -> TeamDashboardResponse:
        request_id = str(uuid.uuid4())
        logger.info(f"Dashboard requested for user {user.id}. Request ID: {request_id}")
        start_time = time.perf_counter()
        
        # Check cache
        if user.id in cls._cache:
            cached_response, timestamp = cls._cache[user.id]
            if time.time() - timestamp < cls.CACHE_TTL_SECONDS:
                logger.info(f"Dashboard Cache HIT for {request_id}")
                return cached_response
                
        logger.info(f"Dashboard Cache MISS for {request_id}. Generating...")
        
        # 1. Fetch DB Context
        context = await DashboardRepository.get_agent_context(session, user)
        
        # 2. Run Agents in Parallel
        agent_responses = await AgentManager.load_all(context)
        
        # 3. Assemble Response
        total_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response = TeamDashboardResponse(
            request_id=request_id,
            total_time_ms=total_time_ms,
            agents=agent_responses
        )
        
        # 4. Save to cache
        cls._cache[user.id] = (response, time.time())
        logger.info(f"Dashboard assembled for {request_id} in {total_time_ms}ms")
        
        return response

    @classmethod
    def invalidate(cls, user_id: str) -> None:
        """Invalidate the in-memory dashboard cache for the given user."""
        cls._cache.pop(user_id, None)


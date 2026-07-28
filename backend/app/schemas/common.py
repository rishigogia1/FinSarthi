from typing import Any, Optional
from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str
    environment: str
    llm_provider: str

class UnavailableResponse(BaseModel):
    available: bool = False
    message: str = "This feature is not available in V1."
    data: Optional[Any] = None

"""
schemas/recommendations.py — Validation models for actions suggestions and feedback collections.
"""
from pydantic import BaseModel, Field, field_validator


class RecommendationResponse(BaseModel):
    title: str
    description: str
    type: str
    priority: str


class RecommendationListResponse(BaseModel):
    recommendations: list[RecommendationResponse]


class InsightFeedbackRequest(BaseModel):
    insight_title: str = Field(..., description="The title of the insight being evaluated")
    feedback_score: int = Field(..., description="Feedback score from 1 (poor) to 5 (excellent)")
    comments: str | None = Field(None, max_length=1000)

    @field_validator("feedback_score")
    @classmethod
    def check_score(cls, v: int) -> int:
        if v < 1 or v > 5:
            raise ValueError("Feedback score must be between 1 and 5 inclusive")
        return v

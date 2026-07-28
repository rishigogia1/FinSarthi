"""
schemas/onboarding.py — Data validation schemas for user onboarding state endpoints.
"""
from pydantic import BaseModel


class OnboardingStepResponse(BaseModel):
    step_id: str
    title: str
    description: str
    completed: bool


class OnboardingStatusResponse(BaseModel):
    onboarding_completed: bool
    steps: list[OnboardingStepResponse]


class OnboardingCompleteRequest(BaseModel):
    completed: bool = True

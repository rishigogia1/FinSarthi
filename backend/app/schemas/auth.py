"""
schemas/auth.py — Pydantic models for authentication request validation and response formatting.
"""
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Full name of the user")
    email: EmailStr = Field(..., description="Unique email address")
    password: str = Field(..., min_length=8, max_length=128, description="Strong password")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: EmailStr) -> str:
        """Strip whitespace and lowercase the email address."""
        return v.strip().lower()


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: EmailStr) -> str:
        """Strip whitespace and lowercase the email address."""
        return v.strip().lower()


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1, description="Opaque refresh token")


class LogoutRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1, description="Opaque refresh token to revoke")


class AuthUserResponse(BaseModel):
    id: str
    name: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token lifetime in seconds")


class AuthResponse(BaseModel):
    user: AuthUserResponse
    tokens: TokenPairResponse


class LogoutResponse(BaseModel):
    success: bool = True

# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError
from app.core.config import Settings

def test_config_missing_required_variables(monkeypatch):
    # Clear necessary env var from environment
    monkeypatch.delenv("DATABASE_URL", raising=False)

    # Disable loading local .env file to check behavior when env is truly missing
    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)

    assert "DATABASE_URL" in str(exc_info.value)

def test_config_invalid_llm_provider(monkeypatch):
    # Mock clean default environment
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost")
    monkeypatch.setenv("REDIS_URL", "redis://localhost")
    monkeypatch.setenv("CHROMA_HOST", "localhost")
    monkeypatch.setenv("CHROMA_PORT", "8000")
    monkeypatch.setenv("JWT_SECRET_KEY", "secret")
    monkeypatch.setenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15")
    monkeypatch.setenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7")
    monkeypatch.setenv("LLM_PROVIDER", "invalid-provider")  # Invalid literal option
    monkeypatch.setenv("GEMINI_API_KEY", "key")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "*")
    monkeypatch.setenv("RATE_LIMIT_LOGIN_ATTEMPTS", "5")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_MINUTES", "15")
    monkeypatch.setenv("ENVIRONMENT", "dev")

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)

    assert "LLM_PROVIDER" in str(exc_info.value)

def test_config_negative_token_expiry(monkeypatch):
    # Mock clean environment but pass an invalid negative JWT token expire
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost")
    monkeypatch.setenv("REDIS_URL", "redis://localhost")
    monkeypatch.setenv("CHROMA_HOST", "localhost")
    monkeypatch.setenv("CHROMA_PORT", "8000")
    monkeypatch.setenv("JWT_SECRET_KEY", "secret")
    monkeypatch.setenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "-10")  # Negative value fails validator
    monkeypatch.setenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7")
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "key")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "*")
    monkeypatch.setenv("RATE_LIMIT_LOGIN_ATTEMPTS", "5")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_MINUTES", "15")
    monkeypatch.setenv("ENVIRONMENT", "dev")

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)

    assert "JWT_ACCESS_TOKEN_EXPIRE_MINUTES" in str(exc_info.value)

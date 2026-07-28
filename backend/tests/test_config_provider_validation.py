import pytest
from pydantic import ValidationError
from app.core.config import Settings

def set_base_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost")
    monkeypatch.setenv("REDIS_URL", "redis://localhost")
    monkeypatch.setenv("CHROMA_HOST", "localhost")
    monkeypatch.setenv("CHROMA_PORT", "8000")
    monkeypatch.setenv("JWT_SECRET_KEY", "secret")
    monkeypatch.setenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15")
    monkeypatch.setenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000")
    monkeypatch.setenv("RATE_LIMIT_LOGIN_ATTEMPTS", "5")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_MINUTES", "15")
    monkeypatch.setenv("ENVIRONMENT", "dev")

def test_missing_openai_key(monkeypatch):
    set_base_env(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)

    assert "OPENAI_API_KEY is required" in str(exc_info.value)

def test_missing_gemini_model(monkeypatch):
    set_base_env(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "some-key")
    monkeypatch.setenv("GEMINI_MODEL", "")

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)

    assert "GEMINI_MODEL is not configured" in str(exc_info.value)

def test_ollama_no_key_required(monkeypatch):
    set_base_env(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # Ensure other provider keys are absent
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("CLAUDE_API_KEY", raising=False)

    settings = Settings(_env_file=None)
    assert settings.LLM_PROVIDER == "ollama"
    assert settings.OLLAMA_BASE_URL == "http://localhost:11434"

def test_cors_origins_parsing(monkeypatch):
    set_base_env(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "some-key")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000, http://localhost:5173, https://finsarthi.app")

    settings = Settings(_env_file=None)
    assert settings.CORS_ALLOWED_ORIGINS == [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://finsarthi.app"
    ]

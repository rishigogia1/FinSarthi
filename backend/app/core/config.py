from typing import Literal, Any
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Core Infrastructure Config
    DATABASE_URL: str
    REDIS_URL: str
    CHROMA_HOST: str
    CHROMA_PORT: int
    
    # Security/Auth Config
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int
    BCRYPT_ROUNDS: int = 12

    # LLM Provider Selection
    LLM_PROVIDER: Literal["gemini", "openai", "claude", "ollama"]

    # Gemini Configuration (Active Provider Option 1)
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GEMINI_TEMPERATURE: float = 0.3
    GEMINI_MAX_TOKENS: int = 4096

    # OpenAI Configuration (Active Provider Option 2)
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o"

    # Claude Configuration (Active Provider Option 3)
    CLAUDE_API_KEY: str | None = None
    CLAUDE_MODEL: str = "claude-sonnet-4-6"

    # Ollama Configuration (Active Provider Option 4)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"

    # CORS Settings (typed as Any to allow custom parsing without triggering automatic pydantic json-list decoding)
    CORS_ALLOWED_ORIGINS: Any

    # Default Localization Settings (Phase 6)
    DEFAULT_CURRENCY: str = "INR"
    DEFAULT_TIMEZONE: str = "Asia/Kolkata"

    # Default Finance Settings (Phase 7)
    DEFAULT_BUDGET_PERIOD: str = "monthly"
    DEFAULT_TRANSACTION_CURRENCY: str = "INR"
    MAX_TRANSACTION_NOTE_LENGTH: int = 500

    # Legacy rate limit fields (kept for backward compat with existing tests)
    RATE_LIMIT_LOGIN_ATTEMPTS: int
    RATE_LIMIT_WINDOW_MINUTES: int

    # Auth-specific rate limit settings (Phase 5)
    AUTH_RATE_LIMIT_LOGIN: int = 5        # max failed login attempts per window
    AUTH_RATE_LIMIT_REGISTER: int = 10    # max register attempts per window
    AUTH_RATE_LIMIT_REFRESH: int = 20     # max refresh attempts per window
    AUTH_RATE_LIMIT_WINDOW_SECONDS: int = 900  # 15-minute window

    # Analytics & Forecasting Config (Phase 8)
    FORECAST_LOOKBACK_MONTHS: int = 6
    FORECAST_MIN_DATA_POINTS: int = 3
    INSIGHT_CACHE_TTL_SECONDS: int = 900
    OPENAI_MODEL_FINANCE_INSIGHTS: str = "gpt-4o"
    MAX_INSIGHTS_PER_RESPONSE: int = 5
    LOW_DATA_THRESHOLD_TRANSACTIONS: int = 10

    # Imports, Sync & Notifications Config (Phase 9)
    MAX_IMPORT_FILE_SIZE_MB: int = 10
    CSV_IMPORT_MAX_ROWS: int = 5000
    IMPORT_PREVIEW_ROW_LIMIT: int = 100
    NOTIFICATION_BATCH_SIZE: int = 100
    REMINDER_LOOKAHEAD_HOURS: int = 24
    EMAIL_NOTIFICATIONS_ENABLED: bool = False
    PUSH_NOTIFICATIONS_ENABLED: bool = False
    DEFAULT_NOTIFICATION_CHANNEL: str = "in_app"

    # Operational Maturity Config (Phase 10)
    APP_VERSION: str = "1.0.0"
    BUILD_SHA: str = "dev"
    BUILD_DATE: str = ""
    IDEMPOTENCY_TTL_SECONDS: int = 3600
    DELIVERY_MAX_RETRIES: int = 3
    DELIVERY_RETRY_BASE_SECONDS: float = 1.0
    RATE_LIMIT_IMPORT_UPLOAD: int = 10
    RATE_LIMIT_INSIGHT_RECOMMENDATIONS: int = 20
    RATE_LIMIT_REMINDER_SCAN: int = 5

    # Polish & Demo Readiness (Phase 11)
    ADMIN_EXPORTS_ENABLED: bool = True
    PDF_EXPORTS_ENABLED: bool = False
    DEMO_MODE_ENABLED: bool = True
    ONBOARDING_ENABLED: bool = True
    AUDIT_LOG_ENABLED: bool = True
    MAX_EXPORT_ROWS: int = 10000

    ENVIRONMENT: Literal["dev", "test", "prod"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    @field_validator(
        "DATABASE_URL",
        "REDIS_URL",
        "CHROMA_HOST",
        "JWT_SECRET_KEY",
    )
    @classmethod
    def cannot_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or blank")
        return v

    @field_validator(
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
        "JWT_REFRESH_TOKEN_EXPIRE_DAYS",
        "RATE_LIMIT_LOGIN_ATTEMPTS",
        "RATE_LIMIT_WINDOW_MINUTES",
        "CHROMA_PORT",
        "BCRYPT_ROUNDS",
        "AUTH_RATE_LIMIT_LOGIN",
        "AUTH_RATE_LIMIT_REGISTER",
        "AUTH_RATE_LIMIT_REFRESH",
        "AUTH_RATE_LIMIT_WINDOW_SECONDS",
    )
    @classmethod
    def must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Must be a positive integer")
        return v

    @field_validator("CORS_ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            # Split comma separated origins and strip spacing
            return [x.strip() for x in v.split(",") if x.strip()]
        if isinstance(v, list):
            return [str(x).strip() for x in v if str(x).strip()]
        return []

    @model_validator(mode="after")
    def validate_active_provider_settings(self) -> "Settings":
        """
        Enforce validation of credentials ONLY for the active provider.
        """
        provider = self.LLM_PROVIDER

        if provider == "gemini":
            if not self.GEMINI_API_KEY or not self.GEMINI_API_KEY.strip():
                raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER is 'gemini'")
            if not self.GEMINI_MODEL or not self.GEMINI_MODEL.strip():
                raise ValueError("GEMINI_MODEL is not configured. Please set GEMINI_MODEL in your .env file.")
        elif provider == "openai":
            if not self.OPENAI_API_KEY or not self.OPENAI_API_KEY.strip():
                raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER is 'openai'")
        elif provider == "claude":
            if not self.CLAUDE_API_KEY or not self.CLAUDE_API_KEY.strip():
                raise ValueError("CLAUDE_API_KEY is required when LLM_PROVIDER is 'claude'")
        elif provider == "ollama":
            if not self.OLLAMA_BASE_URL or not self.OLLAMA_BASE_URL.strip():
                raise ValueError("OLLAMA_BASE_URL is required when LLM_PROVIDER is 'ollama'")

        return self

# Instantiate settings to fail fast if config is missing or malformed
settings = Settings()

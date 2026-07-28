import logging
from contextlib import asynccontextmanager
# pyrefly: ignore [missing-import]
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.database import log_db_connection
from app.core.middleware import RequestLoggingMiddleware, request_id_ctx
from app.core.metrics import metrics
from app.schemas.common import HealthResponse

from app.api.auth.routes import router as auth_router
from app.api.users.routes import router as users_router
from app.api.finance.routes import router as finance_router
from app.api.insights.routes import router as insights_router
from app.api.imports.routes import router as imports_router
from app.api.notifications.routes import router as notifications_router
from app.api.sync.routes import router as sync_router
from app.api.system.routes import router as system_router
from app.api.admin.routes import router as admin_router
from app.api.exports.routes import router as exports_router
from app.api.onboarding.routes import router as onboarding_router
from app.api.demo.routes import router as demo_router
from app.api.chat.routes import router as chat_router
from app.api.planner.routes import router as planner_router
from app.api.coach.routes import router as coach_router
from app.api.dashboard.routes import router as dashboard_router


# Initialize structured logging setup
setup_logging()
logger = logging.getLogger("app.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    active_model = getattr(settings, f"{settings.LLM_PROVIDER.upper()}_MODEL", "N/A")
    logger.info(
        f"Booting FinSarthi Backend | AI Provider: {settings.LLM_PROVIDER.upper()} | Model: {active_model} | Temperature: {settings.GEMINI_TEMPERATURE if settings.LLM_PROVIDER == 'gemini' else 'default'} | Max Tokens: {settings.GEMINI_MAX_TOKENS if settings.LLM_PROVIDER == 'gemini' else 'default'}",
        extra={
            "environment": settings.ENVIRONMENT,
            "llm_provider": settings.LLM_PROVIDER,
            "model": active_model,
            "version": settings.APP_VERSION,
        }
    )

    # Security check: Warning for default JWT secret in production environment
    if settings.ENVIRONMENT == "prod" and settings.JWT_SECRET_KEY == "changeme":
        logger.warning(
            "JWT_SECRET_KEY is still set to 'changeme' in production environment! "
            "Configure a secure secret key immediately."
        )

    # Verify database connectivity at startup (logs host+db only, never password)
    await log_db_connection()

    yield
    # Shutdown tasks
    logger.info("Stopping FinSarthi Backend")

app = FastAPI(
    title="FinSarthi API",
    description="Unified API interface for FinSarthi Multi-Agent Personal Workspace",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# Build the CORS allowed-origins list from settings + essential dev origins.
_cors_origins = list(set(
    settings.CORS_ALLOWED_ORIGINS
    + ["http://localhost:8080", "http://localhost:5173", "http://localhost:3000"]
))

# Middleware order matters: last added = outermost (runs first on request).
# RequestLoggingMiddleware is added FIRST → innermost.
app.add_middleware(RequestLoggingMiddleware)

# CORSMiddleware is added LAST → outermost, so CORS headers are always
# present on every response, even when inner middleware raises exceptions.
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(finance_router, prefix="/api/v1")
app.include_router(insights_router, prefix="/api/v1")
app.include_router(imports_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(sync_router, prefix="/api/v1")
app.include_router(system_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(exports_router, prefix="/api/v1")
app.include_router(onboarding_router, prefix="/api/v1")
app.include_router(demo_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(planner_router, prefix="/api/v1")
app.include_router(coach_router, prefix="/api/v1")



@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Legacy health check endpoint (kept for backward compatibility).
    Canonical operational endpoints live under /api/v1/system/.
    """
    return HealthResponse(
        status="ok",
        environment=settings.ENVIRONMENT,
        llm_provider=settings.LLM_PROVIDER
    )

from fastapi.encoders import jsonable_encoder

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Wrap Pydantic/FastAPI validation errors in the standard error envelope
    so clients always receive a consistent JSON shape.
    """
    rid = request_id_ctx.get("")
    metrics.inc("requests_total", {"method": request.method, "path": request.url.path, "status": "422"})

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "validation_error",
                "message": "Request validation failed",
                "details": jsonable_encoder(exc.errors()),
                "request_id": rid,
            }
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler that captures all uncaught exceptions,
    logs the complete error internally, and returns a client-safe response
    devoid of tracebacks or stack details.
    """
    rid = request_id_ctx.get("")
    metrics.inc("requests_total", {"method": request.method, "path": request.url.path, "status": "500"})

    # Log trace information internally
    logger.exception(
        "Uncaught exception encountered during request processing",
        extra={
            "method": request.method,
            "url": str(request.url),
            "request_id": rid,
        }
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "internal_error",
                "message": "Something went wrong",
                "request_id": rid,
            }
        }
    )

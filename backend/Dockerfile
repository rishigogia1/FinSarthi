# -------------------------------------------------------
# FinSarthi Backend — Multi-stage Docker build
# -------------------------------------------------------
# Python 3.13 slim base. Non-root user for security.
# -------------------------------------------------------
FROM python:3.13-slim AS base

# Prevent .pyc files and enable unbuffered stdout for structured logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies for asyncpg and psycopg2
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# -------------------------------------------------------
# Dependencies stage
# -------------------------------------------------------
FROM base AS dependencies

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# -------------------------------------------------------
# Application stage
# -------------------------------------------------------
FROM dependencies AS app

COPY . .

# Create non-root user
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser && \
    mkdir -p /app/temp_imports && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

# Health check using the liveness endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

"""
test_health.py — Tests for health, readiness, and version system endpoints.
"""
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)


def test_health_endpoint():
    """Legacy /health endpoint returns ok."""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ok"
    assert data["environment"] == settings.ENVIRONMENT
    assert data["llm_provider"] == settings.LLM_PROVIDER


def test_system_health_endpoint():
    """Canonical /api/v1/system/health returns ok."""
    response = client.get("/api/v1/system/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_system_version_endpoint():
    """Version endpoint returns build metadata from config."""
    response = client.get("/api/v1/system/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == settings.APP_VERSION
    assert data["build_sha"] == settings.BUILD_SHA
    assert data["environment"] == settings.ENVIRONMENT
    assert "build_date" in data


def test_system_metrics_endpoint():
    """Metrics endpoint returns snapshot with V1 info warning."""
    response = client.get("/api/v1/system/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "_info" in data
    assert "V1 local" in data["_info"]
    assert "counters" in data
    assert "gauges" in data
    assert "started_at" in data

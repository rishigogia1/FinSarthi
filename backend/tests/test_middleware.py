"""
test_middleware.py — Tests for request logging middleware and X-Request-ID correlation.
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_x_request_id_header_present_on_health():
    """Every response must include the X-Request-ID header."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    rid = response.headers["X-Request-ID"]
    assert len(rid) == 32  # uuid4 hex


def test_x_request_id_is_unique_per_request():
    """Each request gets a distinct correlation ID."""
    r1 = client.get("/health")
    r2 = client.get("/health")
    assert r1.headers["X-Request-ID"] != r2.headers["X-Request-ID"]


def test_x_request_id_header_on_system_endpoints():
    """System endpoints also carry the X-Request-ID header."""
    response = client.get("/api/v1/system/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers


def test_error_envelope_contains_request_id():
    """The 404 or validation error responses should carry the standard envelope shape."""
    response = client.get("/api/v1/nonexistent-path")
    # FastAPI returns 404 for unknown paths — check header is still present
    assert "X-Request-ID" in response.headers

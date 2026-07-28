import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_release_smoke_critical_path(client: AsyncClient):
    """
    Smoke test covering the full critical path of FinSarthi:
    1. Register user
    2. Login user
    3. Create transaction
    4. Fetch forecast insight
    5. Trigger Demo Reset (Phase 11 Feature)
    """
    
    # 1. Register User
    register_response = await client.post(
        "/api/auth/register",
        json={
            "email": "smoketest@example.com",
            "password": "SmokeTest123!",
            "name": "Smoke Tester"
        }
    )
    assert register_response.status_code == 201
    
    # 2. Login User
    login_response = await client.post(
        "/api/auth/login",
        json={
            "email": "smoketest@example.com",
            "password": "SmokeTest123!"
        }
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Create Transaction
    tx_response = await client.post(
        "/api/transactions",
        json={
            "amount": 500.00,
            "type": "EXPENSE",
            "category": "FOOD",
            "date": "2023-10-01T12:00:00Z",
            "description": "Smoke Test Transaction"
        },
        headers=headers
    )
    assert tx_response.status_code == 201
    
    # 4. Fetch Forecast Insight
    insight_response = await client.get(
        "/api/insights/forecast",
        headers=headers
    )
    assert insight_response.status_code == 200
    data = insight_response.json()
    assert "forecast_amount" in data
    assert "explanation" in data
    
    # 5. Phase 11 Feature: Demo Reset
    demo_reset_response = await client.post(
        "/api/demo/reset",
        headers=headers
    )
    assert demo_reset_response.status_code == 200
    demo_data = demo_reset_response.json()
    assert demo_data["status"] == "success"
    assert demo_data["message"] == "Demo data seeded successfully."

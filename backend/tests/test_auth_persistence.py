"""
tests/test_auth_persistence.py — Integration tests for refresh token rotation, logout revocation, and multi-tenant workspace data isolation.
"""
from datetime import date
import pytest
from app.services.analytics_engine import AnalyticsEngine


@pytest.mark.asyncio
async def test_refresh_token_rotation(client, db_session):
    """Verify refresh token rotation issues new access+refresh tokens and revokes old refresh token."""
    reg_payload = {
        "name": "Rotation User",
        "email": "rotation@example.com",
        "password": "Password123!"
    }
    res1 = client.post("/api/v1/auth/register", json=reg_payload)
    assert res1.status_code == 201
    token1 = res1.json()["tokens"]["access_token"]
    refresh1 = res1.json()["tokens"]["refresh_token"]

    # Refresh token pair
    res2 = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh1})
    assert res2.status_code == 200
    token2 = res2.json()["access_token"]
    refresh2 = res2.json()["refresh_token"]

    assert token2 != token1
    assert refresh2 != refresh1

    # Attempting to use old refresh1 fails with 401
    res_old = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh1})
    assert res_old.status_code == 401


@pytest.mark.asyncio
async def test_logout_revocation(client, db_session):
    """Verify logout revokes refresh token in database."""
    reg_payload = {
        "name": "Logout User",
        "email": "logout_user@example.com",
        "password": "Password123!"
    }
    res = client.post("/api/v1/auth/register", json=reg_payload)
    refresh_token = res.json()["tokens"]["refresh_token"]

    # Logout
    logout_res = client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
    assert logout_res.status_code == 200
    assert logout_res.json()["success"] is True

    # Refreshing with revoked token returns 401
    ref_res = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert ref_res.status_code == 401


@pytest.mark.asyncio
async def test_workspace_isolation_alice_vs_bob(client, db_session):
    """
    Verify workspace data isolation:
    1. Alice creates 24 transactions.
    2. Bob registers -> gets completely empty workspace (0 transactions).
    3. Alice logs back in -> all 24 transactions are preserved.
    """
    # 1. Register Alice & Seed 24 Transactions
    alice_reg = client.post("/api/v1/auth/register", json={
        "name": "Alice Workspace",
        "email": "alice@example.com",
        "password": "Password123!"
    })
    alice_id = alice_reg.json()["user"]["id"]
    alice_headers = {"Authorization": f"Bearer {alice_reg.json()['tokens']['access_token']}"}

    today = date.today()
    for i in range(1, 25):
        c_res = client.post("/api/v1/finance/transactions", json={
            "type": "expense",
            "amount": 100.0 + i,
            "category": "Food",
            "occurred_on": str(today),
            "note": f"Alice expense item {i}"
        }, headers=alice_headers)
        assert c_res.status_code == 201

    alice_summary = await AnalyticsEngine.get_financial_summary(db_session, alice_id, today.year, today.month)
    assert alice_summary["history"]["total_tx_count"] == 24

    # 2. Register Bob -> Verify Empty Workspace
    bob_reg = client.post("/api/v1/auth/register", json={
        "name": "Bob Workspace",
        "email": "bob@example.com",
        "password": "Password123!"
    })
    bob_id = bob_reg.json()["user"]["id"]
    bob_headers = {"Authorization": f"Bearer {bob_reg.json()['tokens']['access_token']}"}

    bob_txs = client.get("/api/v1/finance/transactions", headers=bob_headers)
    assert bob_txs.status_code == 200
    assert bob_txs.json()["total"] == 0

    bob_summary = await AnalyticsEngine.get_financial_summary(db_session, bob_id, today.year, today.month)
    assert bob_summary["history"]["total_tx_count"] == 0

    # 3. Alice Logs Back In -> Verify All 24 Transactions Preserved
    alice_login = client.post("/api/v1/auth/login", json={
        "email": "alice@example.com",
        "password": "Password123!"
    })
    assert alice_login.status_code == 200
    alice_headers_new = {"Authorization": f"Bearer {alice_login.json()['tokens']['access_token']}"}

    alice_txs_after = client.get("/api/v1/finance/transactions?page_size=50", headers=alice_headers_new)
    assert alice_txs_after.status_code == 200
    assert alice_txs_after.json()["total"] == 24

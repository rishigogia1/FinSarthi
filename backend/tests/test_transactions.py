"""
tests/test_transactions.py — Integration tests for manual transaction endpoints and validation guards.
"""
from datetime import date, timedelta
import pytest
from sqlalchemy import select
from app.models.transaction import Transaction
from app.services.analytics_engine import AnalyticsEngine


@pytest.mark.asyncio
async def test_transaction_create_success(client, db_session):
    """POST /finance/transactions creates a transaction and updates analytics."""
    reg_payload = {
        "name": "Tx Validation User",
        "email": "tx_val_user@example.com",
        "password": "Password123!"
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    user_id = reg_res.json()["user"]["id"]
    token = reg_res.json()["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "type": "expense",
        "amount": 1500.50,
        "currency": "INR",
        "category": " Food ",
        "occurred_on": str(date.today()),
        "note": " Dinner with friends "
    }
    
    response = client.post(
        "/api/v1/finance/transactions",
        json=payload,
        headers=headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["category"] == "Food"  # cleaned
    assert data["note"] == "Dinner with friends"  # cleaned
    assert data["amount"] == 1500.50
    assert data["type"] == "expense"
    assert "id" in data

    # Verify directly in DB
    stmt = select(Transaction).where(Transaction.id == data["id"])
    res = await db_session.execute(stmt)
    db_tx = res.scalar_one_or_none()
    assert db_tx is not None
    assert db_tx.user_id == user_id


@pytest.mark.asyncio
async def test_transaction_validation_rules(client):
    """POST /finance/transactions rejects invalid amounts and future occurred_on dates."""
    reg_res = client.post("/api/v1/auth/register", json={
        "name": "Rules User",
        "email": "rules_user@example.com",
        "password": "Password123!"
    })
    token = reg_res.json()["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Negative amount
    r1 = client.post(
        "/api/v1/finance/transactions",
        json={"type": "expense", "amount": -10, "category": "Food", "occurred_on": str(date.today())},
        headers=headers
    )
    assert r1.status_code == 422

    # Empty category
    r2 = client.post(
        "/api/v1/finance/transactions",
        json={"type": "expense", "amount": 100, "category": "  ", "occurred_on": str(date.today())},
        headers=headers
    )
    assert r2.status_code == 422

    # Absurd future occurred_on date (e.g. 2 years ahead)
    future_date = date.today() + timedelta(days=700)
    r3 = client.post(
        "/api/v1/finance/transactions",
        json={"type": "income", "amount": 25000, "category": "Salary", "occurred_on": str(future_date)},
        headers=headers
    )
    assert r3.status_code == 422

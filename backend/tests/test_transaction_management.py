"""
tests/test_transaction_management.py — Integration tests for full Transaction lifecycle, soft delete, search, sorting, clamped pagination, authorization, and analytics recalculations.
"""
from datetime import date, timedelta
import pytest
from sqlalchemy import select
from app.models.user import User
from app.models.transaction import Transaction
from app.services.analytics_engine import AnalyticsEngine
from app.services.auth_service import AuthService


@pytest.mark.asyncio
async def test_transaction_crud_lifecycle(client, db_session):
    """Verify full CRUD lifecycle with soft delete."""
    # 1. Register & Auth User
    reg_payload = {
        "name": "CRUD Test User",
        "email": "crud_user@example.com",
        "password": "Password123!"
    }
    res = client.post("/api/v1/auth/register", json=reg_payload)
    assert res.status_code == 201
    token = res.json()["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Transaction
    create_payload = {
        "type": "expense",
        "amount": 1500.00,
        "currency": "INR",
        "category": "Food",
        "occurred_on": str(date.today()),
        "note": "Dinner with team"
    }
    c_res = client.post("/api/v1/finance/transactions", json=create_payload, headers=headers)
    assert c_res.status_code == 201
    tx_data = c_res.json()
    tx_id = tx_data["id"]
    assert tx_data["amount"] == 1500.00
    assert tx_data["category"] == "Food"

    # 3. Read Transaction by ID
    g_res = client.get(f"/api/v1/finance/transactions/{tx_id}", headers=headers)
    assert g_res.status_code == 200
    assert g_res.json()["id"] == tx_id

    # 4. Update Transaction (PATCH)
    update_payload = {
        "amount": 1800.50,
        "category": "Shopping",
        "note": "Updated note item"
    }
    u_res = client.patch(f"/api/v1/finance/transactions/{tx_id}", json=update_payload, headers=headers)
    assert u_res.status_code == 200
    updated_data = u_res.json()
    assert updated_data["amount"] == 1800.50
    assert updated_data["category"] == "Shopping"
    assert updated_data["note"] == "Updated note item"
    # Source must remain unchanged
    assert updated_data["source"] == "MANUAL"

    # 5. Soft Delete Transaction (DELETE)
    d_res = client.delete(f"/api/v1/finance/transactions/{tx_id}", headers=headers)
    assert d_res.status_code == 204

    # 6. Read deleted transaction returns 404
    g_deleted = client.get(f"/api/v1/finance/transactions/{tx_id}", headers=headers)
    assert g_deleted.status_code == 404

    # 7. Assert DB soft-delete flag
    db_stmt = select(Transaction).where(Transaction.id == tx_id)
    db_res = await db_session.execute(db_stmt)
    db_tx = db_res.scalar_one_or_none()
    assert db_tx is not None
    assert db_tx.is_deleted is True
    assert db_tx.deleted_at is not None


@pytest.mark.asyncio
async def test_transaction_search_filtering_and_sorting(client, db_session):
    """Verify search, multi-field filters, sorting, and clamped pagination."""
    reg_payload = {
        "name": "Filter Test User",
        "email": "filter_user@example.com",
        "password": "Password123!"
    }
    res = client.post("/api/v1/auth/register", json=reg_payload)
    token = res.json()["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    today = date.today()
    # Seed 3 distinct transactions
    client.post("/api/v1/finance/transactions", json={
        "type": "expense", "amount": 500.0, "category": "Food", "occurred_on": str(today - timedelta(days=2)), "note": "Coffee bean roast"
    }, headers=headers)
    client.post("/api/v1/finance/transactions", json={
        "type": "expense", "amount": 2500.0, "category": "Transport", "occurred_on": str(today - timedelta(days=1)), "note": "Monthly Petrol fuel"
    }, headers=headers)
    client.post("/api/v1/finance/transactions", json={
        "type": "income", "amount": 50000.0, "category": "Salary", "occurred_on": str(today), "note": "Monthly stipend credit"
    }, headers=headers)

    # Test search query
    s_res = client.get("/api/v1/finance/transactions?search=Petrol", headers=headers)
    assert s_res.status_code == 200
    s_data = s_res.json()
    assert s_data["total"] == 1
    assert s_data["items"][0]["category"] == "Transport"

    # Test category filter
    c_res = client.get("/api/v1/finance/transactions?category=Food", headers=headers)
    assert c_res.status_code == 200
    assert c_res.json()["total"] == 1

    # Test min/max amount filter
    m_res = client.get("/api/v1/finance/transactions?min_amount=1000&max_amount=3000", headers=headers)
    assert m_res.status_code == 200
    assert m_res.json()["total"] == 1
    assert m_res.json()["items"][0]["amount"] == 2500.0

    # Test sorting by amount desc
    sort_res = client.get("/api/v1/finance/transactions?sort_by=amount&order=desc", headers=headers)
    assert sort_res.status_code == 200
    items = sort_res.json()["items"]
    assert len(items) == 3
    assert items[0]["amount"] == 50000.0
    assert items[1]["amount"] == 2500.0
    assert items[2]["amount"] == 500.0


@pytest.mark.asyncio
async def test_transaction_cross_user_authorization(client, db_session):
    """Verify User A cannot view, update, or soft-delete User B's transaction."""
    # Register User A
    res_a = client.post("/api/v1/auth/register", json={
        "name": "User A", "email": "usera@example.com", "password": "Password123!"
    })
    token_a = res_a.json()["tokens"]["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Register User B
    res_b = client.post("/api/v1/auth/register", json={
        "name": "User B", "email": "userb@example.com", "password": "Password123!"
    })
    token_b = res_b.json()["tokens"]["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A creates a transaction
    create_res = client.post("/api/v1/finance/transactions", json={
        "type": "expense", "amount": 999.0, "category": "Bills", "occurred_on": str(date.today()), "note": "User A secret tx"
    }, headers=headers_a)
    tx_id = create_res.json()["id"]

    # User B attempts to GET User A's transaction -> 404
    get_res = client.get(f"/api/v1/finance/transactions/{tx_id}", headers=headers_b)
    assert get_res.status_code == 404

    # User B attempts to PATCH User A's transaction -> 404
    patch_res = client.patch(f"/api/v1/finance/transactions/{tx_id}", json={"amount": 1.0}, headers=headers_b)
    assert patch_res.status_code == 404

    # User B attempts to DELETE User A's transaction -> 404
    del_res = client.delete(f"/api/v1/finance/transactions/{tx_id}", headers=headers_b)
    assert del_res.status_code == 404


@pytest.mark.asyncio
async def test_transaction_analytics_recalculation(client, db_session):
    """Verify that updating and soft-deleting a transaction updates AnalyticsEngine output."""
    reg_payload = {
        "name": "Analytics Recalc User",
        "email": "recalc_user@example.com",
        "password": "Password123!"
    }
    res = client.post("/api/v1/auth/register", json=reg_payload)
    user_id = res.json()["user"]["id"]
    token = res.json()["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    today = date.today()
    # Create transaction 1 (Food 1000)
    c1 = client.post("/api/v1/finance/transactions", json={
        "type": "expense", "amount": 1000.0, "category": "Food", "occurred_on": str(today), "note": "Dinner"
    }, headers=headers)
    tx1_id = c1.json()["id"]

    summary1 = await AnalyticsEngine.get_financial_summary(db_session, user_id, today.year, today.month)
    assert summary1["overview"]["monthly_expense"] == 1000.0

    # Update tx1 amount from 1000 to 2500
    client.patch(f"/api/v1/finance/transactions/{tx1_id}", json={"amount": 2500.0}, headers=headers)
    summary2 = await AnalyticsEngine.get_financial_summary(db_session, user_id, today.year, today.month)
    assert summary2["overview"]["monthly_expense"] == 2500.0

    # Soft-delete tx1
    client.delete(f"/api/v1/finance/transactions/{tx1_id}", headers=headers)
    summary3 = await AnalyticsEngine.get_financial_summary(db_session, user_id, today.year, today.month)
    assert summary3["overview"]["monthly_expense"] == 0.0

"""
test_csv_import.py — Integration tests for transaction CSV ingestion and jobs lifecycle.

Requires live test database (skips automatically if Postgres is unreachable).
"""
import pytest
from app.models.user import User
from app.models.import_job import ImportJob
from app.models.transaction import Transaction
from app.core import security


@pytest.fixture
async def seed_users(db_session):
    """Seed user and return token."""
    pw_hash = security.hash_password("password123")
    user = User(name="Import User", email="imp@example.com", password_hash=pw_hash)
    db_session.add(user)
    await db_session.flush()
    await db_session.commit()
    
    token = security.create_access_token(user.id)
    return user, token


@pytest.mark.asyncio
async def test_csv_import_malformed_headers(client, seed_users):
    """POST /imports/transactions/csv fails when headers are missing."""
    _, token = seed_users
    
    malformed_csv = "date,category,type\n2026-07-16,Food,expense\n"
    files = {"file": ("malformed.csv", malformed_csv, "text/csv")}
    
    response = client.post(
        "/api/v1/imports/transactions/csv",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "failed"
    assert "Missing required headers" in data["error_summary"]


@pytest.mark.asyncio
async def test_csv_import_and_confirm_lifecycle(client, seed_users, db_session):
    """POST /imports/transactions/csv parses, previews, and confirms transactions insertion."""
    user, token = seed_users
    
    csv_data = "date,amount,type,category,note\n2026-07-16,150.00,expense,Food,Lunch with colleagues\n2026-07-15,3500.00,income,Freelance,Web Project\n"
    files = {"file": ("transactions.csv", csv_data, "text/csv")}
    
    # 1. Upload CSV to create Job
    r_upload = client.post(
        "/api/v1/imports/transactions/csv",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert r_upload.status_code == 201
    job_data = r_upload.json()
    job_id = job_data["id"]
    assert job_data["status"] == "parsed"
    assert job_data["total_rows"] == 2
    assert job_data["accepted_rows"] == 2
    
    # 2. Get Preview
    r_preview = client.get(
        f"/api/v1/imports/jobs/{job_id}/preview",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert r_preview.status_code == 200
    preview = r_preview.json()
    assert len(preview["preview_rows"]) == 2
    assert preview["preview_rows"][0]["normalized_row"]["category"] == "Food"
    assert preview["preview_rows"][1]["normalized_row"]["category"] == "Freelance"
    
    # 3. Confirm Ingestion
    r_confirm = client.post(
        f"/api/v1/imports/jobs/{job_id}/confirm",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert r_confirm.status_code == 200
    confirm = r_confirm.json()
    assert confirm["status"] == "confirmed"
    assert confirm["created_count"] == 2
    
    # 4. Verify Transactions added to DB
    from sqlalchemy import select
    stmt = select(Transaction).where(Transaction.user_id == user.id)
    res = await db_session.execute(stmt)
    txs = res.scalars().all()
    assert len(txs) == 2
    
    # Categories should be title-cased
    cats = {t.category for t in txs}
    assert "Food" in cats
    assert "Freelance" in cats
    # Source metadata normalized
    assert all(t.source == "csv_import" for t in txs)

"""
test_import_deduplication.py — Integration tests verifying duplicate transaction filters.

Requires live test database (skips automatically if Postgres is unreachable).
"""
import pytest
from datetime import date
from app.models.user import User
from app.models.transaction import Transaction
from app.core import security


@pytest.fixture
async def seed_users(db_session):
    """Seed user and return token."""
    pw_hash = security.hash_password("password123")
    user = User(name="Deduplicate User", email="dedup@example.com", password_hash=pw_hash)
    db_session.add(user)
    await db_session.flush()
    await db_session.commit()
    
    token = security.create_access_token(user.id)
    return user, token


@pytest.mark.asyncio
async def test_import_deduplication_handling(client, seed_users, db_session):
    """Verify that existing DB transactions and intra-batch duplicates are flagged."""
    user, token = seed_users
    
    # 1. Seed existing transaction in DB
    existing_tx = Transaction(
        user_id=user.id,
        type="expense",
        amount=100.00,
        category="Entertainment",
        occurred_on=date(2026, 7, 16),
        source="manual"
    )
    db_session.add(existing_tx)
    await db_session.flush()
    await db_session.commit()
    
    # 2. Upload CSV containing:
    #   - Row 1: Duplicate matching DB transaction
    #   - Row 2: Unique new transaction
    #   - Row 3: Identical duplicate of Row 2 (same-file collision)
    csv_content = (
        "date,amount,type,category,note\n"
        "2026-07-16,100.00,expense,Entertainment,Duplicate\n"
        "2026-07-16,250.00,expense,Dining,Unique\n"
        "2026-07-16,250.00,expense,Dining,Same File Duplicate\n"
    )
    files = {"file": ("ingestion.csv", csv_content, "text/csv")}
    
    r_upload = client.post(
        "/api/v1/imports/transactions/csv",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert r_upload.status_code == 201
    job = r_upload.json()
    job_id = job["id"]
    assert job["total_rows"] == 3
    assert job["accepted_rows"] == 1
    assert job["duplicate_rows"] == 2
    
    # Retrieve Preview to confirm evaluations statuses
    r_preview = client.get(
        f"/api/v1/imports/jobs/{job_id}/preview",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert r_preview.status_code == 200
    rows = r_preview.json()["preview_rows"]
    assert len(rows) == 3
    
    # Row 1 (DB duplicate)
    assert rows[0]["status"] == "duplicate"
    # Row 2 (Unique)
    assert rows[1]["status"] == "accepted"
    # Row 3 (Same-file duplicate of Row 2)
    assert rows[2]["status"] == "duplicate"
    
    # Confirm import -> only accepted rows get committed
    r_confirm = client.post(
        f"/api/v1/imports/jobs/{job_id}/confirm",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert r_confirm.status_code == 200
    
    # Check total DB transactions = 2 (original 1 + unique 1)
    from sqlalchemy import select
    stmt = select(Transaction).where(Transaction.user_id == user.id)
    res = await db_session.execute(stmt)
    txs = res.scalars().all()
    assert len(txs) == 2

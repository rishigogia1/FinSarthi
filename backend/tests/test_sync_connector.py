"""
test_sync_connector.py — Integration tests verifying bank sync connector stubs.

Requires live test database (skips automatically if Postgres is unreachable).
"""
import pytest
from app.models.user import User
from app.core import security


@pytest.fixture
async def seed_users(db_session):
    """Seed user and return token."""
    pw_hash = security.hash_password("password123")
    user = User(name="Sync User", email="sync@example.com", password_hash=pw_hash)
    db_session.add(user)
    await db_session.flush()
    await db_session.commit()
    
    token = security.create_access_token(user.id)
    return user, token


@pytest.mark.asyncio
async def test_sync_connect_and_accounts_stub(client, seed_users):
    """POST /sync/connect connects successfully and GET /sync/accounts lists accounts mock details."""
    user, token = seed_users
    
    # 1. Test connect stub
    payload = {
        "provider": "plaid",
        "credentials": {"public_token": "mock_token_123"}
    }
    r_conn = client.post(
        "/api/v1/sync/connect",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert r_conn.status_code == 200
    assert r_conn.json()["success"] is True
    assert r_conn.json()["provider"] == "plaid"
    
    # 2. Test list accounts stub
    r_accs = client.get(
        "/api/v1/sync/accounts",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert r_accs.status_code == 200
    accs = r_accs.json()
    assert len(accs) == 2
    assert accs[0]["account_id"] == "acc_mock_01"
    assert accs[0]["balance"] == 145000.50
    assert accs[1]["account_id"] == "acc_mock_02"
    
    # 3. Test trigger sync job
    r_run = client.post(
        "/api/v1/sync/jobs/acc_mock_01/run",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert r_run.status_code == 200
    job = r_run.json()
    assert job["status"] == "completed"
    assert job["job_id"] == "job_mock_123"
    
    # 4. Test trigger sync job on invalid account
    r_fail = client.post(
        "/api/v1/sync/jobs/acc_invalid/run",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert r_fail.status_code == 200
    job_failed = r_fail.json()
    assert job_failed["status"] == "failed"
    assert "Unknown external account" in job_failed["error_message"]

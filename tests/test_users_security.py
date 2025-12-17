import pytest
from unittest.mock import patch, AsyncMock
from app.services.http_client import OrientatiException

# Mock dependencies
@pytest.fixture
def mock_auth_verify():
    with patch("app.services.auth.verify_token") as mock:
        yield mock

@pytest.fixture
def mock_users_service():
    with patch("app.services.users.update_user") as mock_update, \
         patch("app.services.users.delete_user") as mock_delete, \
         patch("app.services.users.change_password") as mock_pwd:
        yield mock_update, mock_delete, mock_pwd

def test_update_user_unauthorized_other_user(client, mock_auth_verify, mock_users_service):
    # User ID 1 tries to update User ID 2
    mock_auth_verify.return_value = {"user_id": 1, "verified": True, "expired": False, "session_id": "sess1"}
    
    response = client.patch(
        "/api/v1/users/2",
        json={"name": "Hacked"},
        headers={"Authorization": "Bearer valid_token"}
    )
    
    # CURRENTLY THIS WILL FAIL (expecting 403, but will probably get 200/500 depending on mock)
    # The vulnerability allows this, so we expect the test to FAIL if the vulnerability exists
    # or PASS if the app handles it correctly. 
    # Since we know it's vulnerable, we write the test to expect the CORRECT behavior (403).
    assert response.status_code == 403, f"Expected 403 Forbidden, got {response.status_code}"

def test_delete_user_unauthorized_other_user(client, mock_auth_verify, mock_users_service):
    # User ID 1 tries to delete User ID 2
    mock_auth_verify.return_value = {"user_id": 1, "verified": True, "expired": False, "session_id": "sess1"}
    
    response = client.delete(
        "/api/v1/users/2",
        headers={"Authorization": "Bearer valid_token"}
    )
    
    assert response.status_code == 403, f"Expected 403 Forbidden, got {response.status_code}"

def test_update_user_authorized_self(client, mock_auth_verify, mock_users_service):
    # User ID 1 tries to update User ID 1
    mock_auth_verify.return_value = {"user_id": 1, "verified": True, "expired": False, "session_id": "sess1"}
    mock_update, _, _ = mock_users_service
    mock_update.return_value = {"name": "Updated"}

    response = client.patch(
        "/api/v1/users/1",
        json={"name": "Updated"},
        headers={"Authorization": "Bearer valid_token"}
    )
    
    assert response.status_code == 200
    mock_update.assert_called_once()

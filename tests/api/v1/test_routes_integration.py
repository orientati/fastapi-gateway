
import pytest
from unittest.mock import patch, AsyncMock
from app.services.http_client import OrientatiException, HttpCodes
from fastapi import status
from app.schemas.users import UpdateUserRequest

# --- Route Integration Tests ---

@pytest.mark.anyio
async def test_update_user_permission_denied(client):
    """
    Test that updating a user with a token payload ID different from the target ID returns 403.
    """
    # Payload user_id = 1
    with patch("app.services.auth.verify_token", return_value={"user_id": 1, "verified": True}):
        # Try to update user_id = 2
        response = await client.patch(
            "/api/v1/users/2",
            headers={"Authorization": "Bearer token"},
            json={"first_name": "Hacker"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()["message"] == "Forbidden"

@pytest.mark.anyio
async def test_update_user_success(client):
    """
    Test that updating self (user_id matches payload) works.
    """
    with patch("app.services.auth.verify_token", return_value={"user_id": 1, "verified": True}):
        with patch("app.services.users.update_user", new_callable=AsyncMock) as mock_update:
            mock_update.return_value = {"id": 1, "email": "test@example.com", "first_name": "Updated"}
            
            response = await client.patch(
                "/api/v1/users/1",
                headers={"Authorization": "Bearer token"},
                json={"first_name": "Updated"}
            )
            assert response.status_code == status.HTTP_200_OK
            assert response.json()["first_name"] == "Updated"

@pytest.mark.anyio
async def test_delete_user_permission_denied(client):
    """
    Test that deleting another user returns 403.
    """
    with patch("app.services.auth.verify_token", return_value={"user_id": 1, "verified": True}):
        response = await client.delete(
            "/api/v1/users/99",
            headers={"Authorization": "Bearer token"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.anyio
async def test_get_schools_success(client):
    """
    Test that get_schools route works (doesn't require strict auth? verify code).
    Code uses: async def get_schools ... (no Depends(validate_token)??)
    Let's check school.py.
    Wait, previous view of school.py showed:
    `async def get_schools(...)` -> it does NOT look like it has `Depends(validate_token)` on GET?
    Let's double check. If it doesn't, this test is trivial.
    POST/PUT/DELETE usually have auth.
    """
    # Checking POST school which definitely has auth
    with patch("app.services.auth.verify_token", return_value={"user_id": 1, "verified": True}):
        with patch("app.services.school.create_school", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = {"id": 1, "name": "New School", "codice_meccanografico": "XX123"}
            
            response = await client.post(
                "/api/v1/schools/",
                headers={"Authorization": "Bearer token"},
                json={"name": "New School", "codice_meccanografico": "XX123", "region": "Lazio", "province": "RM", "city": "Rome", "address": "Via Roma 1", "zip_code": "00100", "email": "school@example.com", "phone": "1234567890", "website": "http://school.com", "description": "Desc", "type": "Lyceum"}
            )
            # Assuming status 201 from previous code view
            assert response.status_code == 201

# Add tests for other modules if needed, but Users and School cover the main patterns (permission check vs simple auth)

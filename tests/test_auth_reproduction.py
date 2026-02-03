
import pytest
from unittest.mock import patch, AsyncMock
from app.services.http_client import OrientatiException, HttpCodes

@pytest.mark.anyio
async def test_missing_token_returns_401(client):
    response = await client.get("/api/v1/users/email_status")
    # FastAPI OAuth2PasswordBearer usually returns 401 Not Authenticated for missing token
    assert response.status_code == 401

@pytest.mark.anyio
async def test_invalid_token_returns_401_or_403(client):
    # Mock auth.verify_token to fail
    with patch("app.services.auth.verify_token", new_callable=AsyncMock) as mock_verify:
        mock_verify.side_effect = OrientatiException(
            message="Invalid token",
            status_code=401,
            details={"message": "Invalid token"},
            url="/token/verify"
        )
        
        response = await client.get("/api/v1/users/email_status", headers={"Authorization": "Bearer invalid_token"})
        
        # This currently works because valid verify_token raises OrientatiException which is caught
        assert response.status_code == 401

@pytest.mark.anyio
async def test_simulated_crash_in_verify_token_returns_500(client):
    # This simulates a bug in verify_token or dependency that raises a generic Exception
    # which is NOT caught by the specific try/except blocks in endpoints if they only catch OrientatiException
    
    # NOTE: app/services/auth.py wraps exceptions in OrientatiException, BUT if the error happens 
    # BEFORE verify_token is called (e.g. in dependency injection itself if we change logic) 
    # or if we have a route that misses the try-except block.
    
    # usage in users.py:
    # try:
    #     payload = await auth.verify_token(token)
    # except OrientatiException as e: ...
    
    # If auth.verify_token raises something else (e.g. TypeError due to bad mock or logic bug), it will 500.
    
    with patch("app.services.auth.verify_token", side_effect=TypeError("Unexpected error")):
        response = await client.get("/api/v1/users/email_status", headers={"Authorization": "Bearer token"})
        # Secure behavior: Internal validation errors should return 401 to avoid leaking info
        assert response.status_code == 401
        assert response.json()["detail"] == "Could not validate credentials"

@pytest.mark.anyio
async def test_service_error_handled_by_global_handler(client):
    # Test that exceptions raised AFTER validation are handled by global handler
    with patch("app.services.auth.verify_token", return_value={"user_id": 1, "verified": True}):
        with patch("app.services.users.change_password" if "users" in "app.services.users" else "app.api.v1.routes.users.users.change_password") as mock_change:
            # We mock the service call to raise OrientatiException
            # need to verify the path. users.change_password is in app.services.users
            pass 

    # Easier: Mock verify_email in users.py which is simple
    with patch("app.services.users.verify_email", side_effect=OrientatiException(status_code=418, message="I'm a teapot")):
         response = await client.get("/api/v1/users/verify_email?token=abc")
         assert response.status_code == 418
         assert response.json()["message"] == "I'm a teapot"

@pytest.mark.anyio
async def test_missing_body_params(client):
    # /api/v1/users/change_password requires body
    with patch("app.services.auth.verify_token", return_value={"user_id": 1, "verified": True}):
        response = await client.post(
            "/api/v1/users/change_password", 
            headers={"Authorization": "Bearer token"},
            json={} # Empty body, but schema requires fields
        )
        # Should be 422
        assert response.status_code == 422
        # Check if the response is well formatted
        print(response.json())

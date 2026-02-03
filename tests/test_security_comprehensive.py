
import pytest
from unittest.mock import patch, AsyncMock
from app.services.http_client import OrientatiException, HttpCodes
from fastapi import status

# --- Security & Exception Handling Tests ---

@pytest.mark.anyio
async def test_missing_authorization_header(client):
    """
    Test that missing Authorization header returns 401.
    """
    response = await client.get("/api/v1/users/email_status")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Not authenticated"}

@pytest.mark.anyio
async def test_malformed_authorization_header_scheme(client):
    """
    Test that Authorization header with wrong scheme (not Bearer) returns 401 or 403.
    FastAPI OAuth2PasswordBearer might treat this strictness differently, likely 401.
    """
    response = await client.get("/api/v1/users/email_status", headers={"Authorization": "Basic token"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Not authenticated"}

@pytest.mark.anyio
async def test_verify_token_expired(client):
    """
    Test that if verify_token returns invalid/expired, we get 401.
    """
    with patch("app.services.auth.verify_token", new_callable=AsyncMock) as mock_verify:
        # Simulate auth service returning 401 for expired token
        mock_verify.side_effect = OrientatiException(
            message="Token expired",
            status_code=401,
            details={"error_code": "TOKEN_EXPIRED"},
            url="/token/verify"
        )
        
        response = await client.get("/api/v1/users/email_status", headers={"Authorization": "Bearer expired_token"})
        
        # Our validate_token dependency catches OrientatiException(401) and re-raises HTTPException(401)
        # preserving the message "Token expired"?
        # Let's check deps.py:
        # if e.status_code in [401, 403]: raise HTTPException(status_code=e.status_code, detail=e.message)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Token expired"

@pytest.mark.anyio
async def test_verify_token_generic_error_fail_secure(client):
    """
    Test that any non-Orientati exception during verification results in a generic 401
    to avoid leaking stack traces or internal errors.
    """
    with patch("app.services.auth.verify_token", side_effect=ValueError("Some internal parsing error")):
        response = await client.get("/api/v1/users/email_status", headers={"Authorization": "Bearer token"})
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        # Must match the generic message in deps.py
        assert response.json()["detail"] == "Could not validate credentials"

@pytest.mark.anyio
async def test_global_handler_internal_server_error(client):
    """
    Test that an unhandled exception in a route (post-auth) returns the sanitized 500 response.
    """
    # Mock auth to succeed
    with patch("app.services.auth.verify_token", return_value={"user_id": 1, "verified": True}):
        # Mock a route handler to crash
        # verify_email is simple enough to mock if we bypass the router? 
        # Easier: Mock a service called by a valid route. 
        # users.email_status calls users.get_email_status_from_token -> mock that.
        with patch("app.services.users.get_email_status_from_token", side_effect=Exception("Database Connection Failed")):
            response = await client.get("/api/v1/users/email_status", headers={"Authorization": "Bearer token"})
            
            assert response.status_code == 500
            data = response.json()
            assert data["message"] == "Internal Server Error"
            assert data["details"] == {"code": "INTERNAL_ERROR"}
            # Ensure no stack trace or "Database Connection Failed" string
            assert "Database Connection Failed" not in str(data)

@pytest.mark.anyio
async def test_validation_error_sanitize(client):
    """
    Test that Pydantic validation errors are sanitized by our validation_exception_handler.
    """
    # POST /change_password requires body.
    # We send invalid body types to trigger Pydantic.
    with patch("app.services.auth.verify_token", return_value={"user_id": 1, "verified": True}):
        response = await client.post(
            "/api/v1/users/change_password", 
            headers={"Authorization": "Bearer token"},
            json={"old_password": "123"} # Missing new_password
        )
        assert response.status_code == 422
        data = response.json()
        assert data["message"] == "Validation Error"
        # Check that 'details' lists the missing field but structure is consistent
        assert isinstance(data["details"], list)
        assert data["details"][0]["loc"] == ["body", "new_password"]
        assert data["details"][0]["msg"] == "Field required"


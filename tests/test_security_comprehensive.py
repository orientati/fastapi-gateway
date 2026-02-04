
import pytest
from unittest.mock import patch, AsyncMock
from app.services.http_client import OrientatiException
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
    Test that Authorization header with wrong scheme (not Bearer) returns 401.
    """
    response = await client.get("/api/v1/users/email_status", headers={"Authorization": "Basic token"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Not authenticated"}

@pytest.mark.anyio
async def test_verify_token_expired(client):
    """
    Test that if verify_token returns 401, we get 401 with the message.
    """
    with patch("app.services.auth.verify_token", new_callable=AsyncMock) as mock_verify:
        mock_verify.side_effect = OrientatiException(
            message="Token expired",
            status_code=401,
            details={"error_code": "TOKEN_EXPIRED"},
            url="/token/verify"
        )
        
        response = await client.get("/api/v1/users/email_status", headers={"Authorization": "Bearer expired_token"})
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Token expired"

@pytest.mark.anyio
async def test_verify_token_generic_error_fail_secure(client):
    """
    **CRITICAL SECURITY TEST**
    Test that any unexpected exception during verification results in generic 401
    to avoid leaking stack traces or internal errors (fail-secure behavior).
    """
    with patch("app.services.auth.verify_token", side_effect=ValueError("Some internal parsing error")):
        response = await client.get("/api/v1/users/email_status", headers={"Authorization": "Bearer token"})
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        # Must match the generic message in deps.py
        assert response.json()["detail"] == "Could not validate credentials"

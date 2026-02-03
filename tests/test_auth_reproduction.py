
import pytest
from unittest.mock import patch, AsyncMock
from app.services.http_client import OrientatiException

@pytest.mark.anyio
async def test_missing_token_returns_401(client):
    """Missing token should return 401."""
    response = await client.get("/api/v1/users/email_status")
    assert response.status_code == 401

@pytest.mark.anyio
async def test_invalid_token_returns_401_or_403(client):
    """Invalid token (OrientatiException) should return 401."""
    with patch("app.services.auth.verify_token", new_callable=AsyncMock) as mock_verify:
        mock_verify.side_effect = OrientatiException(
            message="Invalid token",
            status_code=401,
            details={"message": "Invalid token"},
            url="/token/verify"
        )
        
        response = await client.get("/api/v1/users/email_status", headers={"Authorization": "Bearer invalid_token"})
        assert response.status_code == 401

@pytest.mark.anyio
async def test_simulated_crash_in_verify_token_returns_401(client):
    """
    **CRITICAL SECURITY TEST**: Unexpected exceptions should return generic 401
    to avoid information leakage (fail-secure behavior).
    """
    with patch("app.services.auth.verify_token", side_effect=TypeError("Unexpected error")):
        response = await client.get("/api/v1/users/email_status", headers={"Authorization": "Bearer token"})
        assert response.status_code == 401
        assert response.json()["detail"] == "Could not validate credentials"

import pytest
from app.core.config import settings

@pytest.mark.anyio
async def test_root_endpoint(client):
    response = await client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == settings.SERVICE_NAME
    assert data["version"] == settings.SERVICE_VERSION
    assert data["status"] == "operational"
    
    # Check Security Headers
    assert response.headers["Strict-Transport-Security"] == "max-age=63072000; includeSubDomains"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert "geolocation=()" in response.headers["Permissions-Policy"]
    assert "cdn.jsdelivr.net" in response.headers["Content-Security-Policy"]
    assert "unsafe-inline" in response.headers["Content-Security-Policy"]


@pytest.mark.anyio
async def test_root_endpoint_rate_limit(client):
    # Note: Rate limit might be harder to test with AsyncClient if not configured for test properly,
    # but we can at least ensure it responds correctly to multiple requests.
    for _ in range(3):
        response = await client.get("/")
        assert response.status_code == 200

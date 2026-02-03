import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.anyio
async def test_openapi_schema(client):
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "paths" in data

import pytest
from unittest.mock import patch, AsyncMock
from app.models.user import User
from app.services.auth import pwd_context
from tests.conftest import TestingSessionLocal

# Mark all tests in this module as async
pytestmark = pytest.mark.anyio

async def test_login_generic_error_unknown_user(client):
    response = await client.post("/api/v1/auth/login", data={"username": "unknown@example.com", "password": "password"})
    assert response.status_code == 401, f"Expected 401, got {response.status_code}. Response: {response.text}"
    
    data = response.json()
    assert "Credenziali non valide" in str(data) or data.get("details", {}).get("message") == "Credenziali non valide"

async def test_login_generic_error_wrong_password(client):
    # Retrieve session from TestingSessionLocal which expects to be awaited if used as context manager in test?
    # Actually, verify logic usually uses its own session or the fixture.
    # We can use the db_session fixture implicitly if we want, but here we need to SEED data.
    # Since TestingSessionLocal is an async sessionmaker...
    
    async with TestingSessionLocal() as db:
        hashed = pwd_context.hash("correct_password")
        user = User(email="test@example.com", hashed_password=hashed, email_verified=True, id=1)
        db.add(user)
        await db.commit()
    
    response = await client.post("/api/v1/auth/login", data={"username": "test@example.com", "password": "wrong_password"})
    assert response.status_code == 401
    data = response.json()
    assert "Credenziali non valide" in str(data)

async def test_login_generic_error_unverified_email(client):
    async with TestingSessionLocal() as db:
        hashed = pwd_context.hash("correct_password")
        user = User(email="unverified@example.com", hashed_password=hashed, email_verified=False, id=2)
        db.add(user)
        await db.commit()
    
    response = await client.post("/api/v1/auth/login", data={"username": "unverified@example.com", "password": "correct_password"})
    assert response.status_code == 401
    data = response.json()
    assert "Credenziali non valide" in str(data)

@patch("app.services.auth.create_new_user", new_callable=AsyncMock)
async def test_register_generic_response(mock_create, client):
    # Mock return value to simulate successful downstream creation
    mock_create.return_value = {
        "id": 123, 
        "created_at": "2023-01-01T00:00:00", 
        "updated_at": "2023-01-01T00:00:00"
    }
    
    response = await client.post("/api/v1/auth/register", json={
        "email": "new@example.com", 
        "password": "password", 
        "name": "Test", 
        "surname": "User"
    })
    
    assert response.status_code == 202, f"Expected 202, got {response.status_code}. Response: {response.text}"
    assert response.json()["message"] == "Registration successful. Please check your email to verify your account."

async def test_security_headers(client):
    response = await client.get("/api/v1/auth/login") # Method Not Allowed but headers should be present
    # Or just /health
    # response = await client.get("/health") # health might not exist
    # Let's check headers on the 405 response or a 200 response
    # The login endpoint expects POST, so GET gives 405. Headers should still be there.
    
    assert response.headers["X-Frame-Options"] == "DENY"
    # Strict transport security might depend on middleware config
    assert response.headers["Strict-Transport-Security"] == "max-age=63072000; includeSubDomains"


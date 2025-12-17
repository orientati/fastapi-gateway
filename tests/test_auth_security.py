import pytest
from unittest.mock import patch, AsyncMock
from app.models.user import User
from app.services.auth import pwd_context
from tests.conftest import TestingSessionLocal

def test_login_generic_error_unknown_user(client):
    response = client.post("/api/v1/auth/login", data={"username": "unknown@example.com", "password": "password"})
    assert response.status_code == 401, f"Expected 401, got {response.status_code}. Response: {response.text}"
    # Check that detail structure allows us to see the message or if it's top level
    # The JSONResponse in routes/auth.py puts message inside "content" dict
    # But wait, InvalidCredentialsException raises OrientatiException. 
    # OrientatiException details contain "message".
    # And routes/auth.py returns e.message?
    # Let's check routes/auth.py again.
    # "message": e.message, "details": e.details
    
    data = response.json()
    assert "Credenziali non valide" in str(data) or data.get("details", {}).get("message") == "Credenziali non valide"

def test_login_generic_error_wrong_password(client):
    db = TestingSessionLocal()
    hashed = pwd_context.hash("correct_password")
    # user needs created/updated_at? server_default handles it?
    # sqlite memory might need explicit if strict, but usually ok.
    user = User(email="test@example.com", hashed_password=hashed, email_verified=True, id=1)
    db.add(user)
    db.commit()
    db.close()
    
    response = client.post("/api/v1/auth/login", data={"username": "test@example.com", "password": "wrong_password"})
    assert response.status_code == 401
    data = response.json()
    assert "Credenziali non valide" in str(data)

def test_login_generic_error_unverified_email(client):
    db = TestingSessionLocal()
    hashed = pwd_context.hash("correct_password")
    user = User(email="unverified@example.com", hashed_password=hashed, email_verified=False, id=2)
    db.add(user)
    db.commit()
    db.close()
    
    response = client.post("/api/v1/auth/login", data={"username": "unverified@example.com", "password": "correct_password"})
    assert response.status_code == 401
    data = response.json()
    assert "Credenziali non valide" in str(data)

@patch("app.services.auth.create_new_user", new_callable=AsyncMock)
def test_register_generic_response(mock_create, client):
    # Mock return value to simulate successful downstream creation
    mock_create.return_value = {
        "id": 123, 
        "created_at": "2023-01-01T00:00:00", 
        "updated_at": "2023-01-01T00:00:00"
    }
    
    response = client.post("/api/v1/auth/register", json={
        "email": "new@example.com", 
        "password": "password", 
        "name": "Test", 
        "surname": "User"
    })
    
    assert response.status_code == 202, f"Expected 202, got {response.status_code}. Response: {response.text}"
    assert response.json()["message"] == "Registration successful. Please check your email to verify your account."

def test_security_headers(client):
    response = client.get("/api/v1/auth/login") # Method Not Allowed but headers should be present
    # Or just /health
    response = client.get("/health")
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Strict-Transport-Security"] == "max-age=63072000; includeSubDomains"

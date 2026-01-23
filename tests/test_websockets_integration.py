import pytest
import unittest.mock
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.api.v1.routes.websockets import get_redis_service

@pytest.mark.anyio
async def test_websocket_valid_ticket(client):
    ticket_id = "valid_ticket"
    user_data = {"user_id": "user123"}
    
    # Mock service
    mock_service = AsyncMock()
    mock_service.consume_ws_ticket.return_value = user_data
    
    # Override dependency
    app.dependency_overrides[get_redis_service] = lambda: mock_service

    try:
        with TestClient(app) as tc:
            with tc.websocket_connect(f"/ws?ticket={ticket_id}") as websocket:
                pass
    finally:
         app.dependency_overrides = {}

@pytest.mark.anyio
async def test_websocket_invalid_ticket(client):
    ticket_id = "invalid_ticket"
    
    mock_service = AsyncMock()
    mock_service.consume_ws_ticket.return_value = None
    
    app.dependency_overrides[get_redis_service] = lambda: mock_service

    try:
        with TestClient(app) as tc:
            with pytest.raises(Exception): 
                 with tc.websocket_connect(f"/ws?ticket={ticket_id}") as websocket:
                     pass
            
            mock_service.consume_ws_ticket.assert_called_with(ticket_id)
    finally:
        app.dependency_overrides = {}

@pytest.mark.anyio
async def test_kill_switch_event():
    # Patch AsyncRedisSingleton specifically in auth module because it was already imported
    with unittest.mock.patch("app.services.auth.AsyncRedisSingleton") as MockRedisAuth:
        # Configure mock methods to be awaitable
        MockRedisAuth.return_value.revoke_user_sessions = AsyncMock()
        
        from app.services.auth import handle_session_revocation
        
        user_id = "kill_switch_user"
        event_data = {"user_id": user_id, "reason": "security"}
        
        await handle_session_revocation(event_data)
        
        MockRedisAuth.return_value.revoke_user_sessions.assert_called_with(user_id)


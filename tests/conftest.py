
import pytest
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock, AsyncMock, patch
import sys

# Simpler approach: Mock at module import time before app loads
# This prevents the lifespan from actually connecting to external services

# Mock the external service modules
sys.modules['app.services.broker'] = MagicMock()
sys.modules['app.services.redis_service'] = MagicMock()

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    # Import app after mocks are in place
    from app.main import app
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

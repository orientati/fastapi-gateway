import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import get_db
from app.db.base import Base
from app.main import app

# DB in memoria per i test (aiosqlite)
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(
    bind=engine, 
    class_=AsyncSession,
    autocommit=False, 
    autoflush=False
)

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="function")
async def db_session():
    # Setup DB
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with TestingSessionLocal() as session:
        # Override get_db
        async def override_get_db():
            yield session
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Patch AsyncSessionLocal used in background tasks/consumers
        # We patch the class instantiation to return our session
        # But AsyncSessionLocal() returns a session context manager.
        # So we need a mock that when called returns an async context manager yielding our session.
        class MockSessionContext:
             async def __aenter__(self):
                 return session
             async def __aexit__(self, exc_type, exc_val, exc_tb):
                 pass

        with patch("app.db.session.AsyncSessionLocal", side_effect=MockSessionContext):
            yield session
    
    # Teardown
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="session", autouse=True)
def mock_broker():
    with patch("app.services.broker.AsyncBrokerSingleton") as mock:
        instance = mock.return_value
        instance.connect = AsyncMock(return_value=True)
        instance.close = AsyncMock()
        instance.subscribe = AsyncMock()
        instance.publish_message = AsyncMock()
        yield mock

@pytest.fixture(scope="function", autouse=True)
def mock_redis():
    with patch("app.services.redis_service.AsyncRedisSingleton") as mock:
        instance = mock.return_value
        instance.connect = AsyncMock(return_value=True)
        instance.close = AsyncMock()
        instance.health_check = AsyncMock(return_value=True)
        instance.set_ws_ticket = AsyncMock()
        
        # Default behavior: consume returns None (invalid ticket)
        instance.consume_ws_ticket = AsyncMock(return_value=None)
        
        instance.set_session = AsyncMock()
        instance.revoke_user_sessions = AsyncMock()
        yield mock

@pytest.fixture(scope="function", autouse=True)
def mock_limiter():
    from app.core.limiter import limiter
    # Use MemoryStorage for tests to avoid Redis connection errors
    # We dynamically switch the storage backend of the global limiter instance
    original_storage = limiter.limiter.storage
    
    # We need to import MemoryStorage. 
    # slowapi uses the 'limits' library under the hood.
    from limits.storage import MemoryStorage
    limiter.limiter.storage = MemoryStorage()
    
    yield
    
    # Restore original storage
    limiter.limiter.storage = original_storage


@pytest.fixture(scope="function")
async def client(db_session):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

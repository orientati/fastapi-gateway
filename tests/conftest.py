import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import get_db
from app.db.base import Base
from app.main import app

# DB in memoria per i test
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def db_engine():
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    
    session = TestingSessionLocal(bind=connection)
    
    # Override get_db to use this session
    def override_get_db():
        try:
            yield session
        finally:
            session.close() # Actually we shouldn't close it? Or just not commit?
            # session.commit() # Don't commit if we want rollback? 
            # In FastApi deps, we typically yield. 
            pass

    app.dependency_overrides[get_db] = override_get_db

    # Patch get_db in services because they call it directly
    with patch("app.services.auth.get_db", override_get_db), \
         patch("app.services.users.get_db", override_get_db):
        yield session
    
    session.close()
    transaction.rollback()
    connection.close()
    
@pytest.fixture(scope="session", autouse=True)
def mock_broker():
    with patch("app.services.broker.AsyncBrokerSingleton") as mock:
        instance = mock.return_value
        instance.connect = AsyncMock(return_value=True)
        instance.close = AsyncMock()
        instance.subscribe = AsyncMock()
        instance.publish_message = AsyncMock()
        yield mock

@pytest.fixture(scope="function")
def client(db_session):
    # Base.metadata.create_all(bind=engine) # Already done in db_engine
    # Mock limiter to always allow or be disabled if needed, but enabled=True usually fine with TestClient and our unsafe key_func
    # Force dependency override for get_db again just in case app was re-initialized? 
    # No, app is global.
    with TestClient(app) as c:
        yield c

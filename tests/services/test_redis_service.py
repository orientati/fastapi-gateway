import pytest
import asyncio
from fakeredis import aioredis
from app.services.redis_service import AsyncRedisSingleton

@pytest.fixture
async def real_redis_service():
    # Bypass the singleton for a fresh instance or manually reset it
    AsyncRedisSingleton._instance = None
    service = AsyncRedisSingleton()
    service.client = aioredis.FakeRedis(decode_responses=True)
    yield service
    await service.client.flushall()
    await service.client.aclose()
    AsyncRedisSingleton._instance = None

@pytest.mark.anyio
async def test_set_and_consume_ws_ticket(real_redis_service):
    service = real_redis_service
    ticket_id = "test_ticket"
    data = {"user_id": "user123"}
    
    # 1. Set ticket
    await service.set_ws_ticket(ticket_id, data, ttl=10)
    
    # Verify it exists directly
    val = await service.client.get(f"ws_ticket:{ticket_id}")
    assert val is not None
    
    # 2. Consume ticket
    consumed_data = await service.consume_ws_ticket(ticket_id)
    assert consumed_data == data
    
    # 3. Verify it is gone (Atomic)
    val_after = await service.client.get(f"ws_ticket:{ticket_id}")
    assert val_after is None
    
    # 4. Try to consume again
    consumed_again = await service.consume_ws_ticket(ticket_id)
    assert consumed_again is None

@pytest.mark.anyio
async def test_set_session_and_revocation(real_redis_service):
    service = real_redis_service
    user_id = "user_revocation_test"
    session_id_1 = "sess1"
    session_id_2 = "sess2"
    data = {"some": "data"}
    
    # 1. Set sessions
    await service.set_session(user_id, session_id_1, data)
    await service.set_session(user_id, session_id_2, data)
    
    # Verify sessions exist
    assert await service.client.exists(f"session:{session_id_1}")
    assert await service.client.exists(f"session:{session_id_2}")
    
    # Verify mapping
    user_sessions = await service.client.smembers(f"user_sessions:{user_id}")
    assert session_id_1 in user_sessions
    assert session_id_2 in user_sessions
    
    # 2. Revoke user sessions
    await service.revoke_user_sessions(user_id)
    
    # 3. Verify sessions are gone
    assert not await service.client.exists(f"session:{session_id_1}")
    assert not await service.client.exists(f"session:{session_id_2}")
    assert not await service.client.exists(f"user_sessions:{user_id}")

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status, Depends
from app.services.redis_service import AsyncRedisSingleton
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

async def get_redis_service():
    return AsyncRedisSingleton()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    ticket: str = Query(..., description="One-time use ticket for authentication"),
    redis_service: AsyncRedisSingleton = Depends(get_redis_service)
):
    # redis_service = AsyncRedisSingleton() # Replaced by Dependency
    
    # 1. Validate Ticket (Atomic Consume)
    ticket_data = await redis_service.consume_ws_ticket(ticket)
    
    if not ticket_data:
        logger.warning(f"Invalid or expired ticket used for WebSocket connection: {ticket}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # 2. Accept Connection
    await websocket.accept()
    user_id = ticket_data.get("user_id")
    logger.info(f"WebSocket connected for user {user_id}")

    try:
        while True:
            data = await websocket.receive_text()
            # Echo logic or message handling
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass

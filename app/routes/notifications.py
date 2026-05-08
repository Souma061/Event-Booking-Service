from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.dependencies.auth import get_current_active_user
from app.models.user import User
from app.schemas.notification import NotificationEventType, NotificationPriority
from app.services.kafka_producer import send_notification
from app.utils.websocket_manager import manager

router = APIRouter(prefix="/ws", tags=["notifications"])
api_router = APIRouter(prefix="/api/notifications", tags=["notifications"])

@router.websocket("/notifications/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive, can also receive client messages here if needed
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(user_id)


@api_router.post("/test")
async def send_test_notification(current_user: User = Depends(get_current_active_user)):
    published = await send_notification(
        current_user.id,
        f"Kafka test notification for {current_user.full_name}",
        event_type=NotificationEventType.PAYMENT_SUCCESS,
        booking_id=123,
        data={"source": "manual_test_endpoint"},
        priority=NotificationPriority.HIGH,
    )
    return {
        "published": published,
        "user_id": current_user.id,
        "message": "Test notification queued",
    }

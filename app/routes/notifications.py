from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.utils.websocket_manager import manager

router = APIRouter(prefix="/ws", tags=["notifications"])

@router.websocket("/notifications/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive, can also receive client messages here if needed
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(user_id)

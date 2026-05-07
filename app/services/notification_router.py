from __future__ import annotations

import logging

from app.schemas.notification import NotificationChannel, NotificationEvent
from app.utils.websocket_manager import manager

logger = logging.getLogger(__name__)


class NotificationRouter:
    async def route_event(self, event: NotificationEvent) -> None:
        for channel in event.channels:
            if channel == NotificationChannel.WEBSOCKET:
                await manager.send_personal_json(event.model_dump(mode="json"), event.user_id)
            elif channel == NotificationChannel.EMAIL:
                logger.info("Email notification routing is not implemented for event_id=%s", event.event_id)
            elif channel == NotificationChannel.WHATSAPP:
                logger.info("WhatsApp notification routing is not implemented for event_id=%s", event.event_id)
            else:
                logger.warning("Unsupported notification channel=%s event_id=%s", channel, event.event_id)


notification_router = NotificationRouter()

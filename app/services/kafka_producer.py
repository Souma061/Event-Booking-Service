from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.config import settings
from app.schemas.notification import (
    NotificationChannel,
    NotificationEvent,
    NotificationEventType,
    NotificationPriority,
)

logger = logging.getLogger(__name__)


class KafkaNotificationProducer:
    def __init__(self) -> None:
        self._producer: Any | None = None
        self._started = False
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        if not settings.KAFKA_ENABLE_NOTIFICATIONS:
            logger.info("Kafka notifications are disabled")
            return

        async with self._lock:
            if self._started:
                return

            try:
                from aiokafka import AIOKafkaProducer
            except ImportError:
                logger.warning("aiokafka is not installed. Kafka notifications are disabled.")
                return

            self._producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda value: value.model_dump_json().encode("utf-8"),
                key_serializer=lambda value: str(value).encode("utf-8"),
                request_timeout_ms=5000,
            )
            try:
                await self._producer.start()
                self._started = True
                logger.info("Kafka notification producer connected")
            except Exception:
                logger.exception("Kafka notification producer could not connect")
                try:
                    await self._producer.stop()
                except Exception:
                    logger.debug("Kafka producer cleanup after failed start also failed", exc_info=True)
                self._producer = None
                self._started = False

    async def stop(self) -> None:
        async with self._lock:
            if self._producer and self._started:
                await self._producer.stop()
            self._producer = None
            self._started = False

    async def publish_event(self, event: NotificationEvent) -> bool:
        if not settings.KAFKA_ENABLE_NOTIFICATIONS:
            logger.info("Skipping Kafka notification because the feature is disabled")
            return False

        if not self._started:
            await self.start()

        if not self._producer:
            logger.warning("Kafka producer is unavailable. Dropping notification %s", event.event_id)
            return False

        for attempt in range(1, settings.KAFKA_PRODUCER_RETRIES + 1):
            try:
                await self._producer.send_and_wait(
                    settings.KAFKA_NOTIFICATION_TOPIC,
                    value=event,
                    key=event.user_id,
                )
                logger.info(
                    "Published notification event_id=%s type=%s user_id=%s",
                    event.event_id,
                    event.event_type.value,
                    event.user_id,
                )
                return True
            except Exception:
                logger.exception(
                    "Failed to publish notification event_id=%s attempt=%s",
                    event.event_id,
                    attempt,
                )
                if attempt < settings.KAFKA_PRODUCER_RETRIES:
                    await asyncio.sleep(settings.KAFKA_PRODUCER_RETRY_BACKOFF_SECONDS * attempt)

        return False

    async def health_check(self) -> bool:
        return bool(self._producer and self._started)


kafka_notification_producer = KafkaNotificationProducer()


def _default_channels() -> list[NotificationChannel]:
    channels: list[NotificationChannel] = []
    for raw_channel in settings.NOTIFICATION_DEFAULT_CHANNELS.split(","):
        channel = raw_channel.strip().lower()
        if not channel:
            continue
        try:
            channels.append(NotificationChannel(channel))
        except ValueError:
            logger.warning("Ignoring unsupported notification channel: %s", channel)
    return channels or [NotificationChannel.WEBSOCKET]


async def publish_notification_event(event: NotificationEvent) -> bool:
    return await kafka_notification_producer.publish_event(event)


async def send_notification(
    user_id: int,
    message: str,
    *,
    event_type: NotificationEventType = NotificationEventType.PAYMENT_SUCCESS,
    booking_id: int | None = None,
    data: dict[str, Any] | None = None,
    channels: list[NotificationChannel] | None = None,
    priority: NotificationPriority = NotificationPriority.NORMAL,
) -> bool:
    event = NotificationEvent(
        event_type=event_type,
        user_id=user_id,
        booking_id=booking_id,
        message=message,
        data=data or {},
        channels=channels or _default_channels(),
        priority=priority,
    )
    return await publish_notification_event(event)

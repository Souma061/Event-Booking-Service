from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from app.config import settings
from app.schemas.notification import NotificationEvent
from app.services.notification_router import notification_router

logger = logging.getLogger(__name__)


class KafkaNotificationConsumer:
    def __init__(self) -> None:
        self._consumer: Any | None = None
        self._producer: Any | None = None
        self._running = False

    async def start(self) -> None:
        if not settings.KAFKA_ENABLE_NOTIFICATIONS:
            logger.info("Kafka notification consumer is disabled")
            return

        try:
            from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
        except ImportError:
            logger.warning("aiokafka is not installed. Kafka consumer is disabled.")
            return

        for attempt in range(1, 6):
            self._consumer = AIOKafkaConsumer(
                settings.KAFKA_NOTIFICATION_TOPIC,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id=settings.KAFKA_CONSUMER_GROUP,
                auto_offset_reset=settings.KAFKA_AUTO_OFFSET_RESET,
                enable_auto_commit=False,
                request_timeout_ms=5000,
            )
            self._producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda value: json.dumps(value, default=str).encode("utf-8"),
                request_timeout_ms=5000,
            )
            try:
                await self._consumer.start()
                await self._producer.start()
                self._running = True
                logger.info("Kafka notification consumer connected")
                return
            except Exception:
                logger.exception("Kafka consumer startup failed attempt=%s", attempt)
                await self.stop()
                if attempt < 5:
                    await asyncio.sleep(5)

    async def consume(self) -> None:
        await self.start()
        if not self._consumer:
            return

        try:
            async for message in self._consumer:
                await self.process_message(message)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Kafka notification consumer crashed")
        finally:
            await self.stop()

    async def process_message(self, message: Any) -> None:
        try:
            payload = json.loads(message.value.decode("utf-8"))
            event = NotificationEvent.model_validate(payload)
            await notification_router.route_event(event)
            if self._consumer:
                await self._consumer.commit()
        except Exception as exc:
            logger.exception("Failed to process notification message")
            await self.publish_to_dlq(message, exc)
            if self._consumer:
                await self._consumer.commit()

    async def publish_to_dlq(self, message: Any, error: Exception) -> None:
        if not self._producer:
            return

        raw_value: str
        try:
            raw_value = message.value.decode("utf-8")
        except Exception:
            raw_value = repr(message.value)

        await self._producer.send_and_wait(
            settings.KAFKA_DLQ_TOPIC,
            {
                "topic": message.topic,
                "partition": message.partition,
                "offset": message.offset,
                "error": str(error),
                "raw_value": raw_value,
            },
        )

    async def stop(self) -> None:
        consumer, producer = self._consumer, self._producer
        self._consumer = None
        self._producer = None
        self._running = False

        if consumer:
            await consumer.stop()
        if producer:
            await producer.stop()


kafka_notification_consumer = KafkaNotificationConsumer()


async def consume_notifications() -> None:
    await kafka_notification_consumer.consume()

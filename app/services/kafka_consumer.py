import json
import asyncio
from aiokafka import AIOKafkaConsumer
from app.utils.websocket_manager import manager

async def consume_notifications():
    consumer = AIOKafkaConsumer(
        'notifications',
        bootstrap_servers='localhost:9092',
        group_id="fastapi-notification-group",
        auto_offset_reset="latest" # For learning purposes, skip old messages on startup
    )
    
    # Wait until Kafka is ready, with some retries if needed
    for _ in range(5):
        try:
            await consumer.start()
            print("Successfully connected to Kafka Consumer.")
            break
        except Exception as e:
            print(f"Waiting for Kafka to be ready... {e}")
            await asyncio.sleep(5)
    else:
        print("Failed to start Kafka consumer after retries.")
        return

    try:
        async for msg in consumer:
            try:
                data = json.loads(msg.value.decode('utf-8'))
                user_id = data.get('user_id')
                notification_text = data.get('message')
                
                if user_id and notification_text:
                    print(f"Consumed Kafka msg for user {user_id}: {notification_text}")
                    # Broadcast to specific user via WebSocket
                    await manager.send_personal_message(notification_text, user_id)
            except Exception as e:
                print(f"Error processing Kafka message: {e}")
    finally:
        await consumer.stop()

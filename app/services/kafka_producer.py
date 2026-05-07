import json
from aiokafka import AIOKafkaProducer

async def send_notification(user_id: int, message: str):
    producer = AIOKafkaProducer(bootstrap_servers='localhost:9092')
    await producer.start()
    try:
        payload = {"user_id": user_id, "message": message}
        await producer.send_and_wait("notifications", json.dumps(payload).encode('utf-8'))
    except Exception as e:
        print(f"Failed to send Kafka notification: {e}")
    finally:
        await producer.stop()

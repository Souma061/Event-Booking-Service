# Kafka Notification Walkthrough

This file explains the Kafka push notification setup in this project from a beginner point of view.

## What Kafka Is Doing Here

Kafka is acting like a durable message pipe between the booking/payment API and the websocket notification system.

Without Kafka, the API would need to send the notification directly while handling the request. With Kafka, the API only publishes an event like "payment succeeded" to a Kafka topic. A separate consumer reads that event and sends it to the user over websocket.

This keeps the API flow cleaner:

```text
User action
  -> FastAPI route
  -> publish notification event to Kafka
  -> Kafka stores event in a topic
  -> FastAPI Kafka consumer reads event
  -> consumer sends event to websocket
  -> user receives realtime notification
```

## Important Kafka Words

### Broker

The Kafka server. In this project it runs inside Docker as:

```text
event-booking-kafka
```

### Topic

A named stream of messages. This project uses:

```text
notification.requested
notification.dlq
```

`notification.requested` is the main topic. Valid notification events go here.

`notification.dlq` is the dead-letter queue. Broken messages go here so they are not lost.

### Producer

Something that writes messages to Kafka.

In this project, producers are:

- The FastAPI app, through `app/services/kafka_producer.py`
- Your manual terminal test using `kafka-console-producer.sh`

### Consumer

Something that reads messages from Kafka.

In this project, the consumer is:

```text
app/services/kafka_consumer.py
```

It reads from `notification.requested`.

### Consumer Group

A named group of consumers that share work. This project uses:

```text
notification-service
```

Kafka tracks what this group has already processed.

### DLQ

DLQ means dead-letter queue.

If the consumer cannot process a message, it publishes an error record to:

```text
notification.dlq
```

Example bad message:

```text
not-json
```

That is not valid JSON, so the consumer cannot convert it into a notification event.

## Why There Is No ZooKeeper

Older Kafka setups used ZooKeeper to manage cluster metadata.

This project uses Kafka in KRaft mode, which means Kafka manages its own metadata. No ZooKeeper container is needed.

The Docker Compose file uses:

```yaml
KAFKA_PROCESS_ROLES: broker,controller
```

That means one Kafka container is acting as both:

- broker: handles client messages
- controller: manages Kafka metadata

This is good for local development.

## Files In This Project

### `docker-compose.kafka.yml`

Starts Kafka and Kafka UI.

Services:

- `kafka`: the actual Kafka broker in KRaft mode
- `kafka-init`: creates the topics
- `kafka-ui`: browser UI at `http://localhost:8080`

### `app/schemas/notification.py`

Defines the notification event shape.

Example:

```json
{
  "event_id": "test-1",
  "event_type": "payment_success",
  "timestamp": "2026-05-07T00:00:00Z",
  "user_id": 1,
  "booking_id": 123,
  "message": "Kafka push notification test",
  "data": {
    "ticket_codes": ["TKT-123"]
  },
  "channels": ["websocket"],
  "priority": "high"
}
```

### `app/services/kafka_producer.py`

Publishes notification events to Kafka.

The app calls `send_notification(...)`.

That creates a structured notification event and sends it to:

```text
notification.requested
```

### `app/services/kafka_consumer.py`

Reads messages from:

```text
notification.requested
```

For each message, it:

1. Decodes JSON.
2. Validates the notification schema.
3. Sends the event to `notification_router`.
4. Commits the Kafka offset.

If processing fails, it writes an error record to:

```text
notification.dlq
```

### `app/services/notification_router.py`

Routes a valid notification event to the right channel.

Right now, websocket is implemented:

```text
channels: ["websocket"]
```

Email and WhatsApp are placeholders for future routing.

### `app/utils/websocket_manager.py`

Tracks connected websocket users.

If user `1` is connected to:

```text
ws://localhost:8000/ws/notifications/1
```

then a notification with:

```json
"user_id": 1
```

is sent to that websocket connection.

## Full Local Testing Process

### 1. Activate Python Environment

```bash
source venv/bin/activate
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

This is needed because the backend uses:

```text
aiokafka
```

### 3. Start Kafka

```bash
docker compose -f docker-compose.kafka.yml up -d
```

### 4. Check Topics

```bash
docker exec -it event-booking-kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --list
```

Expected:

```text
notification.dlq
notification.requested
```

### 5. Start Backend

```bash
uvicorn main:app --reload
```

This starts:

- the FastAPI API
- the Kafka producer connection
- the Kafka consumer task
- the websocket route

### 6. Connect Websocket

In a separate terminal:

```bash
wscat -c ws://localhost:8000/ws/notifications/1
```

This means:

```text
I am user 1, waiting for realtime notifications.
```

### 7. Send A Valid Kafka Message Manually

In another terminal:

```bash
docker exec -it event-booking-kafka /opt/kafka/bin/kafka-console-producer.sh \
  --bootstrap-server localhost:9092 \
  --topic notification.requested
```

When you see:

```text
>
```

paste:

```json
{"event_id":"test-1","event_type":"payment_success","timestamp":"2026-05-07T00:00:00Z","user_id":1,"booking_id":123,"message":"Kafka push notification test","data":{"ticket_codes":["TKT-123"]},"channels":["websocket"],"priority":"high"}
```

Then press Enter.

Expected websocket output:

```json
{"event_id":"test-1","event_type":"payment_success","timestamp":"2026-05-07T00:00:00Z","user_id":1,"booking_id":123,"message":"Kafka push notification test","data":{"ticket_codes":["TKT-123"]},"channels":["websocket"],"priority":"high"}
```

This proves:

```text
Kafka -> FastAPI consumer -> websocket
```

is working.

### 8. Send A Bad Message

Use the same producer command:

```bash
docker exec -it event-booking-kafka /opt/kafka/bin/kafka-console-producer.sh \
  --bootstrap-server localhost:9092 \
  --topic notification.requested
```

When you see:

```text
>
```

paste:

```text
not-json
```

Then press Enter.

This is intentionally broken.

### 9. Read The DLQ

In another terminal:

```bash
docker exec -it event-booking-kafka /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic notification.dlq \
  --from-beginning
```

Expected output looks like:

```json
{"topic": "notification.requested", "partition": 2, "offset": 0, "error": "Expecting value: line 1 column 1 (char 0)", "raw_value": "not-json"}
```

This proves:

```text
bad Kafka message -> consumer catches error -> DLQ
```

is working.

## What Happens In The Real App

### Booking Created

When a user creates a booking, `app/routes/booking.py` calls `send_notification(...)`.

It publishes an event like:

```text
booking_created
```

to Kafka.

### Payment Success

When payment is verified or confirmed by webhook, `app/routes/payments.py` calls `send_notification(...)`.

It publishes:

```text
payment_success
```

with ticket data.

### Booking Expired

If a booking stays unpaid for 15 minutes, the expiration task publishes:

```text
booking_expired
```

## How To Think About This System

The API does not directly say:

```text
send websocket now
```

Instead it says:

```text
something happened
```

Kafka stores that fact.

The consumer reacts to that fact and sends the websocket message.

That is event-driven architecture.

## Useful Commands

### Start Kafka

```bash
docker compose -f docker-compose.kafka.yml up -d
```

### Stop Kafka

```bash
docker compose -f docker-compose.kafka.yml down
```

### List Topics

```bash
docker exec -it event-booking-kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --list
```

### Produce Message

```bash
docker exec -it event-booking-kafka /opt/kafka/bin/kafka-console-producer.sh \
  --bootstrap-server localhost:9092 \
  --topic notification.requested
```

### Consume DLQ

```bash
docker exec -it event-booking-kafka /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic notification.dlq \
  --from-beginning
```

### Inspect Consumer Group

```bash
docker exec -it event-booking-kafka /opt/kafka/bin/kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --describe \
  --group notification-service
```

### Open Kafka UI

```text
http://localhost:8080
```

## Common Problems

### `kafka-console-producer.sh` Not Found

Use the full path:

```bash
/opt/kafka/bin/kafka-console-producer.sh
```

The official Apache Kafka Docker image does not put all scripts in `$PATH`.

### Websocket Gets Nothing

Check:

1. Backend is running with `uvicorn main:app --reload`.
2. `wscat` is connected to the matching user id.
3. Kafka message has the same `user_id`.
4. Message has `"channels":["websocket"]`.
5. Kafka consumer did not crash.

### Message Goes To DLQ

That means the consumer could not process it.

Usually the message is:

- not valid JSON
- missing required fields
- has invalid event type
- has invalid channel

## Current Status

Working:

- Kafka in KRaft mode
- no ZooKeeper
- topic creation
- producer
- consumer
- websocket delivery
- DLQ handling

Future work:

- email routing through Kafka
- WhatsApp routing through Kafka
- database notification logs
- notification preferences
- retries per notification channel

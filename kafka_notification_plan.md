# Kafka Push Notification System - Architecture Plan

## Context

The Event Booking Service currently has basic notification infrastructure with email services and a NotificationLog database model. However, notifications are handled synchronously within the main application flow, which creates several issues:

- **Tight Coupling**: Notification logic is embedded in business logic
- **Scalability**: Synchronous notification processing slows down API responses
- **Reliability**: No retry mechanism for failed notifications
- **Flexibility**: Difficult to add new notification channels
- **Monitoring**: Limited visibility into notification delivery

The goal is to implement a Kafka-based event-driven notification system that decouples notification processing from the main application, improves reliability, and enables scalable multi-channel notifications.

## Current Infrastructure Analysis

### Existing Components
- **Kafka Setup**: Already configured in docker-compose.yml with topics:
  - `notification.requested` (3 partitions)
  - `notification.dlq` (1 partition)
- **Kafka Client**: `aiokafka==0.13.0` already in requirements.txt
- **Notification Services**:
  - `app/services/email_services.py` - Email notifications
  - `app/services/whatsapp_services.py` - Empty placeholder
- **Database Model**: `NotificationLog` table for tracking notifications
- **Background Tasks**: FastAPI BackgroundTasks for async operations

### Current Notification Triggers
1. **Booking Creation**: `app/routes/booking.py` - Line 160
2. **Payment Confirmation**: `app/routes/payments.py` - Lines 332, 407
3. **Booking Expiration**: `app/routes/booking.py` - Line 23

## Proposed Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────────────┐
│                     Event Booking Service                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐        │
│  │   Booking   │    │   Payment   │    │    Admin     │        │
│  │   Service    │    │   Service   │    │   Service    │        │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘        │
│         │                   │                   │                 │
│         └───────────────────┼───────────────────┘                 │
│                             │                                     │
│                    ┌────────▼────────┐                           │
│                    │  Event Publisher │                          │
│                    │   (Kafka Producer)                         │
│                    └────────┬────────┘                           │
└─────────────────────────────┼─────────────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   Kafka Cluster  │
                    │                  │
                    │ notification.    │
                    │   requested      │
                    │                  │
                    │ notification.    │
                    │      dlq         │
                    └────────┬─────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼────────┐  ┌───────▼────────┐  ┌───────▼────────┐
│  Notification   │  │  Notification   │  │  Notification   │
│  Consumer 1     │  │  Consumer 2     │  │  Consumer N     │
│  (Email)        │  │  (WhatsApp)    │  │  (Push)         │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
┌────────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐
│  Email Service  │  │ WhatsApp Service│  │  Push Service   │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### Core Components

#### 1. Event Publisher (Kafka Producer)
**Location**: `app/services/kafka_producer_service.py`

**Responsibilities**:
- Initialize and manage Kafka producer connection
- Publish notification events to `notification.requested` topic
- Handle serialization and error handling
- Implement retry logic for failed publishes

**Event Types**:
```python
enum NotificationEventType:
    BOOKING_CREATED = "booking_created"
    BOOKING_CONFIRMED = "booking_confirmed"
    BOOKING_CANCELLED = "booking_cancelled"
    BOOKING_EXPIRED = "booking_expired"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    TICKET_ISSUED = "ticket_issued"
    REMINDER_EVENT = "reminder_event"
```

**Event Schema**:
```python
{
    "event_id": "uuid",
    "event_type": "booking_created",
    "timestamp": "iso8601",
    "user_id": 123,
    "booking_id": 456,
    "data": {
        "event_title": "Concert",
        "show_time": "iso8601",
        "venue": "Stadium",
        "tickets": ["TKT-1", "TKT-2"],
        "total_amount": "999.00"
    },
    "channels": ["email", "whatsapp"],
    "priority": "high"
}
```

#### 2. Notification Consumer Service
**Location**: `app/services/kafka_consumer_service.py`

**Responsibilities**:
- Initialize and manage Kafka consumer connection
- Subscribe to `notification.requested` topic
- Process events and route to appropriate notification services
- Handle errors and publish to DLQ if needed
- Implement consumer group management for scalability

**Consumer Groups**:
- `email-notification-group` - For email notifications
- `whatsapp-notification-group` - For WhatsApp notifications
- `push-notification-group` - For push notifications

#### 3. Notification Router
**Location**: `app/services/notification_router.py`

**Responsibilities**:
- Route events to appropriate notification channels
- Filter events based on user preferences
- Apply business rules (rate limiting, quiet hours)
- Coordinate multiple channel notifications

#### 4. Enhanced Notification Services
**Locations**:
- `app/services/email_services.py` (enhance existing)
- `app/services/whatsapp_services.py` (implement)
- `app/services/push_services.py` (new)

**Responsibilities**:
- Implement channel-specific notification logic
- Handle template rendering
- Manage delivery status
- Implement retry logic

#### 5. Notification Configuration
**Location**: `app/config.py` (enhance)

**New Settings**:
```python
KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
KAFKA_NOTIFICATION_TOPIC: str = "notification.requested"
KAFKA_DLQ_TOPIC: str = "notification.dlq"
KAFKA_CONSUMER_GROUP: str = "notification-service"
KAFKA_AUTO_OFFSET_RESET: str = "earliest"
KAFKA_ENABLE_NOTIFICATIONS: bool = True
NOTIFICATION_DEFAULT_CHANNELS: list[str] = ["email"]
NOTIFICATION_QUIET_HOURS_ENABLED: bool = False
NOTIFICATION_QUIET_HOURS_START: str = "22:00"
NOTIFICATION_QUIET_HOURS_END: str = "08:00"
```

## Implementation Plan

### Phase 1: Core Infrastructure (Week 1)

#### 1.1 Kafka Producer Service
**File**: `app/services/kafka_producer_service.py`

**Key Functions**:
```python
class KafkaNotificationProducer:
    async def initialize()
    async def publish_event(event: NotificationEvent)
    async def close()
    async def health_check()
```

**Integration Points**:
- Initialize in `app/main.py` startup event
- Inject into routes via dependency injection
- Graceful shutdown in cleanup event

#### 1.2 Event Schemas
**File**: `app/schemas/notification.py`

**Schema Definitions**:
```python
class NotificationEvent(BaseModel):
    event_id: str
    event_type: NotificationEventType
    timestamp: datetime
    user_id: int
    booking_id: int | None = None
    data: dict[str, Any]
    channels: list[str]
    priority: str = "normal"

class NotificationDelivery(BaseModel):
    channel: str
    status: str
    error_message: str | None = None
    retry_count: int = 0
```

#### 1.3 Configuration Updates
**File**: `app/config.py`

**Add Kafka Configuration**:
- Bootstrap servers
- Topic names
- Consumer group settings
- Feature flags

### Phase 2: Consumer Service (Week 2)

#### 2.1 Kafka Consumer Service
**File**: `app/services/kafka_consumer_service.py`

**Key Functions**:
```python
class KafkaNotificationConsumer:
    async def initialize()
    async def start_consuming()
    async def process_message(message)
    async def handle_error(message, error)
    async def publish_to_dlq(message, error)
    async def close()
```

#### 2.2 Notification Router
**File**: `app/services/notification_router.py`

**Key Functions**:
```python
class NotificationRouter:
    async def route_event(event: NotificationEvent)
    async def get_user_channels(user_id: int) -> list[str]
    async def apply_business_rules(event: NotificationEvent)
    async def is_quiet_hours() -> bool
```

#### 2.3 Enhanced Email Service
**File**: `app/services/email_services.py`

**Enhancements**:
- Template-based email rendering
- Async processing with proper error handling
- Delivery status tracking
- Retry logic with exponential backoff

#### 2.4 WhatsApp Service Implementation
**File**: `app/services/whatsapp_services.py`

**Implementation**:
- WhatsApp Business API integration
- Template message support
- Media handling for QR tickets
- Delivery receipt processing

### Phase 3: Integration (Week 3)

#### 3.1 Booking Flow Integration
**File**: `app/routes/booking.py`

**Integration Points**:
- Line 160: Publish `booking_created` event
- Line 23: Publish `booking_expired` event
- Replace background tasks with Kafka events

#### 3.2 Payment Flow Integration
**File**: `app/routes/payments.py`

**Integration Points**:
- Line 332: Publish `payment_success` event
- Line 407: Publish `payment_success` event (webhook)
- Line 206: Publish `ticket_issued` event
- Replace email background tasks with Kafka events

#### 3.3 Admin Flow Integration
**File**: `app/routes/admin.py`

**Integration Points**:
- Line 69: Publish `ticket_verified` event
- Add notification for failed verifications

### Phase 4: Push Notifications (Week 4)

#### 4.1 Push Service
**File**: `app/services/push_services.py`

**Implementation**:
- Web Push API integration
- VAPID key generation
- Subscription management
- Push notification formatting

#### 4.2 Push Subscription Management
**File**: `app/routes/push_subscriptions.py`

**New Endpoints**:
- `POST /api/push/subscribe` - Register push subscription
- `DELETE /api/push/unsubscribe` - Remove subscription
- `GET /api/push/subscriptions` - List user subscriptions

#### 4.3 Database Schema Updates
**File**: `alembic/versions/xxx_add_push_subscriptions.py`

**New Table**:
```python
class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    endpoint: Mapped[str] = mapped_column(String(500))
    p256dh_key: Mapped[str] = mapped_column(String(255))
    auth_key: Mapped[str] = mapped_column(String(255))
    user_agent: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

### Phase 5: Frontend Integration (Week 5)

#### 5.1 Push Subscription UI
**File**: `Client/src/components/PushNotificationManager.tsx`

**Features**:
- Request notification permission
- Subscribe to push notifications
- Manage subscription preferences
- Display notification history

#### 5.2 Service Worker
**File**: `Client/public/sw.js`

**Implementation**:
- Push event handling
- Notification display
- Background sync
- Click handling

#### 5.3 Notification Preferences
**File**: `Client/src/pages/NotificationPreferences.tsx`

**Features**:
- Channel selection (email, WhatsApp, push)
- Event type preferences
- Quiet hours configuration
- Test notification sending

## Data Flow Examples

### Booking Creation Flow

```
1. User creates booking
   ↓
2. BookingService.create_booking()
   ↓
3. Database transaction commits
   ↓
4. KafkaProducer.publish_event({
     event_type: "booking_created",
     user_id: 123,
     booking_id: 456,
     data: {...},
     channels: ["email", "whatsapp"]
   })
   ↓
5. Event published to notification.requested topic
   ↓
6. KafkaConsumer receives event
   ↓
7. NotificationRouter.route_event()
   ↓
8. EmailService.send_booking_confirmation()
   WhatsAppService.send_booking_confirmation()
   ↓
9. NotificationLog entries created
   ↓
10. User receives notifications
```

### Payment Success Flow

```
1. Payment webhook received
   ↓
2. PaymentService._confirm_cashfree_payment()
   ↓
3. Booking status updated to CONFIRMED
   ↓
4. Tickets generated
   ↓
5. KafkaProducer.publish_event({
     event_type: "payment_success",
     user_id: 123,
     booking_id: 456,
     data: {
       tickets: ["TKT-1", "TKT-2"],
       total_amount: "999.00"
     },
     channels: ["email", "push"]
   })
   ↓
6. Event published to notification.requested topic
   ↓
7. Multiple consumers process event:
   - EmailConsumer: Sends confirmation with tickets
   - PushConsumer: Sends push notification
   ↓
8. User receives email and push notification
```

## Error Handling Strategy

### Producer Errors
- **Connection Errors**: Retry with exponential backoff
- **Serialization Errors**: Log and alert monitoring
- **Timeout Errors**: Circuit breaker pattern

### Consumer Errors
- **Transient Errors**: Retry with exponential backoff (max 3 attempts)
- **Permanent Errors**: Publish to DLQ for manual inspection
- **Deserialization Errors**: Log raw message and publish to DLQ

### Notification Service Errors
- **Service Unavailable**: Queue for retry
- **Rate Limiting**: Implement backoff and retry
- **Invalid Data**: Log and skip, continue processing

### DLQ Monitoring
- **Alerting**: Monitor DLQ size and alert on threshold
- **Inspection**: Tool for inspecting DLQ messages
- **Reprocessing**: Mechanism to reprocess DLQ messages

## Monitoring & Observability

### Metrics to Track
1. **Producer Metrics**
   - Events published per minute
   - Publish latency
   - Publish error rate
   - Producer connection status

2. **Consumer Metrics**
   - Messages consumed per minute
   - Consumer lag
   - Processing time
   - Error rate by channel

3. **Notification Metrics**
   - Delivery rate by channel
   - Delivery latency
   - Retry rate
   - Failed notifications

### Logging Strategy
- **Structured Logging**: JSON format with correlation IDs
- **Event Logging**: Log all published events
- **Error Logging**: Detailed error context
- **Performance Logging**: Processing times

### Health Checks
- **Producer Health**: Connection status, publish test
- **Consumer Health**: Connection status, consumer lag
- **Service Health**: External service availability

## Security Considerations

### Kafka Security
- **Authentication**: SASL/PLAIN or SSL
- **Authorization**: ACLs for topic access
- **Encryption**: SSL/TLS for data in transit

### Data Privacy
- **PII Handling**: Minimize personal data in events
- **Data Retention**: Configure appropriate retention policies
- **Compliance**: GDPR considerations for user data

### API Security
- **Push Subscriptions**: Validate and authenticate
- **User Preferences**: Secure storage and access
- **Rate Limiting**: Prevent abuse

## Testing Strategy

### Unit Tests
- **Producer Service**: Mock Kafka client, test event publishing
- **Consumer Service**: Mock Kafka streams, test event processing
- **Notification Services**: Mock external APIs, test notification logic
- **Router Service**: Test routing logic and business rules

### Integration Tests
- **End-to-End**: Test complete notification flow
- **Kafka Integration**: Test with real Kafka instance
- **Error Scenarios**: Test error handling and DLQ
- **Performance**: Test under load

### Contract Tests
- **Event Schemas**: Validate event structure
- **API Contracts**: Test API integration points
- **Consumer Contracts**: Test consumer expectations

## Deployment Strategy

### Development Environment
- **Local Kafka**: Use docker-compose Kafka
- **Single Consumer**: Run one consumer instance
- **Debug Logging**: Enable detailed logging

### Staging Environment
- **Production-like Kafka**: Use staging Kafka cluster
- **Multiple Consumers**: Test consumer group scaling
- **Monitoring**: Enable full monitoring stack

### Production Environment
- **Rolling Deployment**: Deploy consumers gradually
- **Feature Flags**: Enable Kafka notifications gradually
- **Monitoring**: Full observability stack
- **Alerting**: Comprehensive alerting setup

## Rollback Plan

### Immediate Rollback
- **Feature Flag**: Disable Kafka notifications
- **Fallback**: Revert to synchronous notifications
- **Data Consistency**: Ensure no data loss

### Graceful Degradation
- **Producer Fallback**: Log events if Kafka unavailable
- **Consumer Fallback**: Queue events if consumer down
- **Service Fallback**: Skip failed channels, continue others

## Performance Considerations

### Throughput Requirements
- **Expected Load**: 1000 notifications/minute peak
- **Kafka Capacity**: Current setup supports 10K+ messages/second
- **Consumer Scaling**: Horizontal scaling with consumer groups

### Latency Requirements
- **Target Latency**: < 5 seconds from event to notification
- **P95 Latency**: < 10 seconds
- **P99 Latency**: < 30 seconds

### Resource Optimization
- **Batch Processing**: Batch events where possible
- **Connection Pooling**: Reuse Kafka connections
- **Async Processing**: Fully async implementation

## Future Enhancements

### Short-term (3-6 months)
- **Notification Templates**: Rich template system
- **User Preferences**: Granular notification controls
- **Analytics**: Notification engagement tracking
- **A/B Testing**: Test notification content

### Long-term (6-12 months)
- **Multi-language**: Support for multiple languages
- **Personalization**: ML-based notification timing
- **Rich Media**: Images, videos in notifications
- **Interactive Notifications**: Actionable notifications

## Critical Files to Modify

### Backend Files
1. `app/config.py` - Add Kafka configuration
2. `app/main.py` - Initialize producer/consumer
3. `app/services/kafka_producer_service.py` - New file
4. `app/services/kafka_consumer_service.py` - New file
5. `app/services/notification_router.py` - New file
6. `app/services/email_services.py` - Enhance existing
7. `app/services/whatsapp_services.py` - Implement
8. `app/services/push_services.py` - New file
9. `app/schemas/notification.py` - New file
10. `app/routes/booking.py` - Integrate producer
11. `app/routes/payments.py` - Integrate producer
12. `app/routes/admin.py` - Integrate producer
13. `app/routes/push_subscriptions.py` - New file

### Database Files
1. `alembic/versions/xxx_add_push_subscriptions.py` - New migration

### Frontend Files
1. `Client/src/components/PushNotificationManager.tsx` - New file
2. `Client/src/pages/NotificationPreferences.tsx` - New file
3. `Client/public/sw.js` - New file
4. `Client/src/types/index.ts` - Add notification types

### Configuration Files
1. `docker-compose.yml` - Already configured
2. `requirements.txt` - Already has aiokafka
3. `.env` - Add Kafka environment variables

## Verification Plan

### Manual Testing
1. **Booking Flow**: Create booking and verify notifications
2. **Payment Flow**: Complete payment and verify notifications
3. **Error Scenarios**: Test error handling and DLQ
4. **Performance**: Test under load

### Automated Testing
1. **Unit Tests**: Test individual components
2. **Integration Tests**: Test complete flows
3. **Contract Tests**: Validate event schemas
4. **Load Tests**: Test performance under load

### Monitoring Verification
1. **Metrics**: Verify all metrics are collected
2. **Logs**: Verify structured logging
3. **Alerts**: Verify alerting setup
4. **Health Checks**: Verify health endpoints

## Success Criteria

### Functional Requirements
- ✅ All notification types working via Kafka
- ✅ Multi-channel notifications supported
- ✅ Error handling and DLQ working
- ✅ Push notifications functional
- ✅ User preferences respected

### Non-Functional Requirements
- ✅ < 5 second notification latency
- ✅ 99.9% uptime for notification service
- ✅ Support for 1000+ notifications/minute
- ✅ Zero data loss
- ✅ Comprehensive monitoring

### Business Requirements
- ✅ Improved user engagement
- ✅ Reduced support tickets
- ✅ Better notification deliverability
- ✅ Scalable architecture
- ✅ Cost-effective solution

## Conclusion

This Kafka-based push notification system will transform the Event Booking Service's notification capabilities from a synchronous, tightly-coupled implementation to an asynchronous, event-driven architecture. The system will provide better scalability, reliability, and flexibility while maintaining the existing functionality and adding new capabilities like push notifications and multi-channel support.

The phased implementation approach ensures minimal risk and allows for gradual rollout and testing. The architecture is designed to handle current requirements while being flexible enough to accommodate future enhancements.

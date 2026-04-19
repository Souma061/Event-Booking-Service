# Project Analysis — Event Booking Service

## Project Type

**FastAPI (Python) backend API** for an event booking platform, backed by **PostgreSQL** via SQLAlchemy ORM. The service is designed to handle event creation, show scheduling, seat inventory management, ticket booking with payments (Razorpay), QR-code tickets, and notifications (email/WhatsApp).

**Tech Stack:**
- **Framework:** FastAPI
- **ORM:** SQLAlchemy 2.0 (mapped_column style)
- **Database:** PostgreSQL (psycopg2-binary)
- **Migrations:** Alembic (listed in requirements, not yet configured)
- **Auth:** JWT (python-jose) + bcrypt (passlib)
- **Payments:** Razorpay
- **QR Codes:** qrcode[pil]
- **Email:** aiosmtplib (async SMTP)
- **HTTP Client:** httpx (for WhatsApp/external APIs)
- **Validation:** Pydantic v2 + pydantic-settings
- **Rate Limiting:** Custom token-bucket implementation (in-memory) + slowapi (listed in requirements)
- **Testing:** pytest + pytest-asyncio

---

## What Has Been Built So Far

### ✅ Project Structure & Configuration
- Well-organized package layout (`app/models`, `app/routes`, `app/schemas`, `app/services`, `app/utils`)
- `app/config.py` — Pydantic-settings based config loading from `.env` with sensible defaults for JWT, rate limits, Razorpay, SMTP, and feature flags

### ✅ Database Layer
- `app/database.py` — SQLAlchemy engine, session factory, `get_db()` dependency generator, and a `db_transaction()` context manager

### ✅ Data Models (Complete)
| Model                    | Table                      | Status |
|--------------------------|----------------------------|--------|
| `User`                   | `users`                    | ✅ Done |
| `Venue`                  | `venues`                   | ✅ Done |
| `Event`                  | `events`                   | ✅ Done |
| `Show`                   | `shows`                    | ✅ Done |
| `SeatCategoryInventory`  | `seat_category_inventory`  | ✅ Done |
| `Booking`                | `bookings`                 | ✅ Done |
| `BookingItem`            | `booking_items`            | ✅ Done |
| `Payment`                | `payments`                 | ✅ Done |
| `Ticket`                 | `tickets`                  | ✅ Done |
| `NotificationLog`        | `notification_logs`        | ✅ Done |

### ✅ Enums
- `UserRole` (ADMIN, CUSTOMER)
- `BookingStatus` (PENDING_PAYMENT, CONFIRMED, CANCELLED, FAILED)
- `PaymentStatus` (CREATED, CAPTURED, FAILED, REFUNDED)
- `TicketStatus` (ACTIVE, USED, CANCELLED, EXPIRED)

### ✅ Pydantic Schemas (Request/Response DTOs)
- **Auth:** `RegisterRequest`, `LoginRequest`, `Userout`, `TokenResponse`
- **Events:** `VenueCreate`, `VenueOut`, `EventCreta`, `EventOut`, `ShowCreate`, `ShowOut`, `InventoryRowIn`, `InventoryRowOut`, `ShowAvailabilityOut`
- **Booking:** `BookingItemIn`, `BookingCreateRequest`, `BookingItemOut`, `BookingOut`
- **Payment:** `PaymentOrderCreateRequest`, `PaymentOrderOut`, `PaymentVerificationRequest`, `PaymentVerificationOut`
- **Recommendation:** `RecommendationOut`, `RecommendationResponse`

### ✅ Utilities
- `app/utils/security.py` — Password hashing/verification (bcrypt), JWT creation/verification
- `app/utils/rate_limit.py` — Custom in-memory Token Bucket rate limiter with separate buckets for login (5 tokens, 1/12s refill) and booking (3 tokens, 1/20s refill)

### ✅ Entry Point
- `main.py` (root) imports the app from `app/main.py`
- `app/main.py` has a basic FastAPI instance with a health-check `/` route

---

## What Needs to Be Built

### 🔴 Route Handlers (ALL EMPTY)
These files exist but contain no code:

| File                     | Expected Functionality |
|--------------------------|------------------------|
| `app/routes/auth.py`     | `POST /register`, `POST /login`, `GET /me` |
| `app/routes/events.py`   | CRUD for Venues, Events, Shows, Seat Inventory; list/search/filter events; show availability |
| `app/routes/booking.py`  | Create booking (with idempotency), list user bookings, cancel booking |
| `app/routes/payments.py` | Create Razorpay order, verify payment callback/webhook, handle refunds |

### 🔴 Services (ALL EMPTY)
| File                            | Expected Functionality |
|---------------------------------|------------------------|
| `app/services/email_services.py`    | Send booking confirmation, ticket, and cancellation emails via aiosmtplib |
| `app/services/qr_services.py`      | Generate QR codes for tickets (using `qrcode[pil]`) |
| `app/services/whatsapp_services.py` | Send WhatsApp notifications (behind `FEATURE_WHATSAPP_ENABLED` flag) |

### 🔴 Auth Dependency
- No `get_current_user` / `get_current_admin` FastAPI dependency for protecting routes (needs to decode JWT from `Authorization: Bearer <token>` header)

### 🔴 Router Registration
- `app/main.py` does **not** include/register any of the route modules — routers need to be mounted on the app

### 🔴 Middleware
- No CORS middleware configured (needed for frontend integration)
- No rate-limiting middleware wired into FastAPI (the token-bucket utility exists but isn't applied)
- No request logging / error handling middleware

### 🔴 Database Migrations
- Alembic is in `requirements.txt` but no `alembic/` directory or `alembic.ini` exists — migrations are not set up

### 🔴 Recommendation Engine
- Schemas exist (`RecommendationOut`, `RecommendationResponse`) but no route or service logic
- Config has a `FEATURE_LLM_RECOMMENDATIONS` flag suggesting an LLM-based approach is planned

### 🔴 Testing
- pytest & pytest-asyncio are in requirements but no test files exist

---

## Bugs & Issues Found

| # | Location | Issue |
|---|----------|-------|
| 1 | `app/models/user.py` | **Typo:** Column is named `passwird_hash` — should be `password_hash` |
| 2 | `app/schemas/event.py` | **Typo:** Schema class named `EventCreta` — should be `EventCreate` |
| 3 | `app/models/booking.py` | **Relationship naming:** `Payment.Booking` uses capital `B` — should be `Payment.booking` (lowercase) to match convention |
| 4 | `app/schemas/payment.py` | **Wrong types:** `PaymentVerificationRequest.provider_order_id` and `provider_payment_id` are typed as `int` — Razorpay IDs are strings (e.g., `order_ABC123`) |
| 5 | `app/schemas/reccomendation.py` | **Typo in filename:** `reccomendation.py` — should be `recommendation.py` |

---

## Suggestions & Recommendations

### Architecture
1. **Add an `app/dependencies.py`** — Centralize common FastAPI dependencies (`get_current_user`, `get_current_admin`, `get_db`) for cleaner route code
2. **Add an `app/exceptions.py`** — Define custom exception classes (e.g., `SeatUnavailableError`, `BookingExpiredError`) and register global exception handlers
3. **Use APIRouter with prefixes** — Each route file should use `APIRouter(prefix="/api/...", tags=["..."])` and be included in `app/main.py`

### Booking Flow
4. **Implement optimistic locking or `SELECT ... FOR UPDATE`** on `SeatCategoryInventory.available_seats` to prevent overselling under concurrent bookings
5. **Add a booking expiry mechanism** — A background task (or cron) to auto-cancel `PENDING_PAYMENT` bookings after a timeout (e.g., 15 minutes) and release seats

### Payments
6. **Implement a Razorpay webhook endpoint** (`POST /api/payments/webhook`) in addition to client-side verification for reliability
7. **Store raw webhook payloads** in `Payment.raw_upload` for audit/debugging

### Security
8. **Add refresh tokens** — The current setup only has access tokens; add refresh token rotation for better security
9. **Add role-based access control** — Ensure admin-only routes (event creation, etc.) check `user.role == ADMIN`

### DevOps & Quality
10. **Set up Alembic** — Run `alembic init alembic` and create an initial migration
11. **Add a `docker-compose.yml`** — For local PostgreSQL + the app, making onboarding easier
12. **Add a `.env.example`** — Document all required environment variables
13. **Write tests** — Start with auth and booking flows; use an in-memory SQLite or test PostgreSQL database
14. **Add CI pipeline** — GitHub Actions or similar for lint + test on every push

### Scaling (Future)
15. **Move rate-limit state to Redis** (as noted in `rate_limit.py` comments) for multi-process/multi-instance deployments
16. **Add pagination** to list endpoints (events, bookings)
17. **Add search/filter** capabilities for events (by category, city, date range)
18. **Add an admin dashboard API** for event analytics and booking reports

---

## Suggested Build Order (Next Steps)

1. **Fix the typos/bugs** listed above
2. **Set up Alembic** and generate the initial migration
3. **Build `app/routes/auth.py`** — Register, login, get-current-user dependency
4. **Build `app/routes/events.py`** — CRUD for venues, events, shows, inventory
5. **Build `app/routes/booking.py`** — Create booking with seat locking, list, cancel
6. **Build `app/services/qr_services.py`** — QR code generation for tickets
7. **Build `app/routes/payments.py`** + Razorpay integration
8. **Build `app/services/email_services.py`** — Confirmation emails
9. **Wire up middleware** (CORS, rate limiting, error handlers)
10. **Write tests**
11. **Build recommendation engine** (optional / future)
12. **Build WhatsApp notifications** (optional / future)

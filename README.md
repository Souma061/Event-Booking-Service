# Event Booking Service

A full-stack event booking application built with FastAPI (backend) and React (frontend) with TypeScript. This service allows users to browse events, book tickets, manage bookings, and process payments securely.

## Features

- User authentication (registration, login, admin access)
- Event browsing and filtering
- Ticket booking with seat selection
- Secure payment processing (Cashfree integration)
- Admin dashboard for event and booking management
- Email notifications for booking confirmations
- Rate limiting for security
- Responsive design for mobile and desktop

## Folder Structure

```
Event_Booking_Service/
├── app/                     # Backend (FastAPI)
│   ├── api/                 # API route definitions
│   ├── core/                # Core configurations
│   ├── db/                  # Database models and schemas
│   ├── services/            # Business logic services
│   └── utils/               # Utility functions
├── Client/                  # Frontend (React + TypeScript)
│   ├── public/              # Static assets
│   └── src/                 # Source code
│       ├── components/      # Reusable UI components
│       ├── context/         # React context (Auth, etc.)
│       ├── lib/             # API client and utilities
│       ├── pages/           # Page components
│       └── styles/          # CSS and styling
├── alembic/                 # Database migration scripts
├── tests/                   # Test files
├── scripts/                 # Deployment and utility scripts
├── requirements.txt         # Python dependencies
├── package.json             # Frontend dependencies
└── README.md                # This file
```

## Requirements

### Backend
- Python 3.8+
- PostgreSQL
- Redis (for rate limiting and caching)

### Frontend
- Node.js 14+
- npm or yarn

## Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/Event_Booking_Service.git
cd Event_Booking_Service
```

### 2. Backend Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration:
#   DATABASE_URL, SECRET_KEY, CASHFREE_APP_ID, etc.

# Run database migrations
alembic upgrade head

# Start the development server
uvicorn app.main:app --reload
```

### 3. Frontend Setup
```bash
cd Client
npm install

# Create environment file
cp .env.example .env
# Edit .env with your configuration:
#   VITE_API_URL=http://localhost:8000

# Start the development server
npm run dev
```

## Environment Variables

### Backend (.env)
```
APP_NAME=Event Booking Service
DEBUG=True
DATABASE_URL=postgresql://user:password@localhost/event_booking
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ALLOW_ORIGINS=["http://localhost:5173"]
CASHFREE_APP_ID=your_cashfree_app_id
CASHFREE_SECRET_KEY=your_cashfree_secret_key
CASHFREE_ENVIRONMENT=sandbox
RATE_LIMIT_LOGIN=5/minute
RATE_LIMIT_BOOKING=3/minute
VALKEY_URL=redis://localhost:6379
RATE_LIMIT_FAIL_OPEN=True
ADMIN_SECRET_KEY=your-admin-secret-key
```

### Frontend (Client/.env)
```
VITE_API_URL=http://localhost:8000
VITE_CASHFREE_MODE=sandbox
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/admin/login` - Admin login
- `GET /api/auth/me` - Get current user info

### Events
- `GET /api/events/` - List events
- `GET /api/events/{event_id}` - Get event details
- `POST /api/events/` - Create event (Admin)
- `PUT /api/events/{event_id}` - Update event (Admin)
- `DELETE /api/events/{event_id}` - Delete event (Admin)

### Bookings
- `GET /api/bookings/` - List user bookings
- `POST /api/bookings/` - Create a booking
- `GET /api/bookings/{booking_id}` - Get booking details
- `PUT /api/bookings/{booking_id}/cancel` - Cancel booking

### Payments
- `POST /api/payments/` - Initiate payment
- `POST /api/payments/cashfree/webhook` - Cashfree webhook endpoint

## Monitoring and Metrics

The application includes built-in monitoring capabilities for production deployments:

### Health Checks
- `GET /health` - Basic health check endpoint
- `GET /api/auth/health` - Authentication service health
- `GET /api/events/health` - Events service health

### Key Metrics Tracked
- **Performance Metrics**
  - API response times (p95, p99)
  - Requests per second (RPS)
  - Error rates (4xx, 5xx)
  - Database query latency

- **Business Metrics**
  - Daily active users (DAU)
  - Booking conversion rate
  - Revenue per event
  - Ticket sales volume
  - Cancellation rate

- **System Metrics**
  - CPU and memory usage
  - Database connection pool usage
  - Redis cache hit/miss ratio
  - Queue depths (if using message queues)

### Monitoring Stack (Production)
- **Metrics Collection**: Prometheus with custom endpoints
- **Visualization**: Grafana dashboards
- **Logging**: Structured JSON logs with ELK stack (Elasticsearch, Logstash, Kibana)
- **Distributed Tracing**: OpenTelemetry for request tracing
- **Alerting**: AlertManager for notifications via Slack/email

### Implementation Notes
1. Backend includes Prometheus metrics endpoints at `/metrics`
2. Frontend tracks vitals and custom events via analytics library
3. All services emit structured logs to stdout for container orchestration
4. Health checks are used by Kubernetes/liveness probes
5. Custom business metrics are emitted via application instrumentation

## Testing

### Backend Tests
The backend uses pytest for testing. Tests are located in the `tests/` directory.

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py

# Run tests in verbose mode
pytest -v
```

### Frontend Tests
The frontend uses Vitest for testing. Tests are located alongside the source files in the `Client/src/` directory with `.test.tsx` or `.test.ts` extensions.

```bash
# Run all tests
cd Client
npm run test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage
```

### Test Types
- **Unit Tests**: Test individual functions and components in isolation
- **Integration Tests**: Test API endpoints and service interactions
- **End-to-End Tests**: Test complete user flows (planned for future implementation)

## Load Test & Scalability Report

> Tests were conducted using [Locust 2.43.4](https://locust.io/) against a local FastAPI backend (PostgreSQL + Redis).  
> Test file: `tests/load/locustfile.py` | Runner: `scripts/run_load_tests.sh`

### Test Scenarios

| Scenario | Users (weight) | What it tests |
|---|---|---|
| **BrowseUser** | 5× | Anonymous read traffic — events, categories, availability |
| **AuthUser** | 3× | Full auth flow — register → browse → book |
| **BookingRace** | 2× | Concurrent seat grabs on the same show (DB locking) |
| **LoginHammer** | 1× | Brute-force bad logins — rate limiter stress |
| **RegistrationFlood** | 1× | Mass registrations — bcrypt / DB write throughput |
| **HealthPoller** | 1× | `/health` liveness probes under mixed load |

---

### Results Across All Test Runs

#### Run 1 — Smoke Test (10 users · 1 worker · 20 s)

| Metric | Value |
|---|---|
| Total requests | 344 |
| Throughput | ~15.7 req/s |
| p50 latency | 88ms |
| p95 latency | 210ms |
| Real failures | 0 (0%) |
| Booking race failures | 0 |

**Finding:** Clean baseline. All "failures" were `429` rate-limit responses from the shared localhost IP — expected in test environments.

---

#### Run 2 — Normal Load (100 users · 4 workers · 60 s)

| Metric | Before (1 worker) | After (4 workers) | Δ |
|---|---|---|---|
| Throughput | 18 req/s | **94.8 req/s** | +427% |
| p50 latency | 1700ms | **130ms** | 13× faster |
| p95 latency | 9300ms | **420ms** | 22× faster |
| `/health` p50 | 9300ms | **180ms** | 51× faster |
| Real failures | timeouts | **0** | — |

**Finding:** Single-worker bottleneck confirmed. 4 workers resolved all queue saturation at 100 users.

---

#### Run 3 — Spike Test (500 users · 33 workers · 90 s) ✅ Final

| Metric | 4 workers (prev) | 33 workers (final) | Δ |
|---|---|---|---|
| Total requests | 19,740 | **95,591** | +384% |
| Throughput | 205 req/s | **1,013 req/s** | +394% |
| p50 latency | 560ms | **4ms** | 140× faster |
| p95 latency | 3,100ms | **44ms** | 70× faster |
| p99 latency | 3,900ms | **120ms** | 32× faster |
| `/health` p50 | 3,200ms | **4ms** | 800× faster |
| Booking race (`/api/bookings [race]`) | 0 / 1,137 | **0 / 46,576** | ✅ |
| Real failures | 74 (0.37%) | **1 (0.001%)** | — |

**All 114 reported "failures" were `429` rate-limit responses** from shared localhost IP — expected behavior. Only **1 genuine connection drop** occurred across 95,591 requests.

---

### Endpoint Performance (Spike Test — 33 workers)

| Endpoint | p50 | p95 | p99 | req/s |
|---|---|---|---|---|
| `POST /api/bookings [race]` | 3ms | 32ms | 77ms | 493 |
| `POST /api/auth/login` | 4ms | 58ms | 110ms | 37 |
| `POST /api/auth/register [flood]` | 4ms | 65ms | 150ms | 55 |
| `GET /api/events` | 4ms | 60ms | 180ms | 69 |
| `GET /health` | 4ms | 52ms | 140ms | 121 |
| `GET /api/bookings/shows/{id}/availability` | 4ms | 63ms | 230ms | 44 |

---

### Optimisations Applied

| Change | Impact |
|---|---|
| **Async password hashing** (`run_in_executor`) | Auth routes no longer block the event loop during CPU-bound hashing |
| **Async `/health`** | Health endpoint is never queued behind synchronous handlers |
| **In-process TTL cache (15 s)** on events list, categories, venues | Eliminated repeated DB hits on the most-read endpoints |
| **Cache invalidation on write** | New events/venues appear immediately; cache stays consistent |
| **33 uvicorn workers** `(2 × nproc + 1)` | Optimal CPU utilisation across 16 physical cores |
| **Shared Redis rate limiter** (`VALKEY_URL`) | Rate-limit state shared across all workers in multi-process deployments |

---

### Rate Limiting Architecture

| Layer | Limit | Key |
|---|---|---|
| Global (all routes) | 120 / minute | Client IP |
| Login / Admin login | 10 / minute | IP + email |
| Booking creation | 5 / minute | IP + user ID |

IP extraction respects `cf-connecting-ip` → `x-real-ip` → `x-forwarded-for` → direct connection, ensuring correct behaviour behind Cloudflare, Nginx, and load balancers.

---

### How to Reproduce

```bash
# Install Locust
pip install locust

# Start backend (replace 33 with your (2×nproc)+1)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 33

# Run a test profile
bash scripts/run_load_tests.sh smoke      # quick sanity check
bash scripts/run_load_tests.sh normal     # 100 users, 60 s
bash scripts/run_load_tests.sh spike      # 500 users, 90 s  ← main stress test
bash scripts/run_load_tests.sh race       # booking contention only
bash scripts/run_load_tests.sh ui         # interactive dashboard at :8089
```

HTML reports are saved to `tests/load/reports/`.

---

## Deployment


### Production Build
```bash
# Backend (using Gunicorn)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app

# Frontend
cd Client
npm run build
# Serve the dist/ folder with your preferred static file server
```

### Docker Deployment
Dockerfiles and docker-compose.yml can be added for containerized deployment.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

Soumabrata Ghosh - [soumabrataghosh57@gmail.com](mailto:soumabrataghosh57@gmail.com)

Project Link: [https://github.com/Souma061/Event-Booking-Service](https://github.com/yourusername/Event_Booking_Service)

Live Link: [https://event-booking-service.vercel.app/](https://event-booking-service.vercel.app/)

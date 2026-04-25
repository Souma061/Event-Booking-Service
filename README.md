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

Your Name - [your.email@example.com](mailto:your.email@example.com)

Project Link: [https://github.com/yourusername/Event_Booking_Service](https://github.com/yourusername/Event_Booking_Service)
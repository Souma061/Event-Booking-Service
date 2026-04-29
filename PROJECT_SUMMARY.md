# Project Summary: Event Booking Service

## Overview
The **Event Booking Service** is a full-stack platform designed for event discovery, ticket booking, and management. It features a FastAPI-based backend and a React (TypeScript) frontend.

## Tech Stack
### Backend
- **Framework:** FastAPI
- **Database:** PostgreSQL (SQLAlchemy ORM)
- **Migrations:** Alembic
- **Authentication:** JWT (JSON Web Tokens), OAuth (Google, GitHub)
- **Rate Limiting:** Custom implementation using token buckets, with Redis/Valkey support
- **Testing:** Pytest

### Frontend
- **Framework:** React 19 (TypeScript)
- **Build Tool:** Vite
- **Styling:** TailwindCSS
- **State Management:** React Context (AuthContext)
- **API Client:** Axios

## Completed Features
- [x] User Registration and Login
- [x] Admin Dashboard for Event Management
- [x] Event Listing and Detail Pages
- [x] Ticket Booking Workflow with Seat Selection
- [x] OAuth Integration (Google, GitHub)
- [x] Payment Gateway Integration (Cashfree)
- [x] Rate Limiting on critical endpoints (Login, Booking)
- [x] Health Checks and Monitoring Endpoints
- [x] Responsive Mobile-First UI
- [x] Security Hardening:
    - [x] Transitioned to HTTP-Only, Secure Cookies for authentication.
    - [x] Enhanced Request Validation (whitespace stripping, phone regex).
    - [x] Added `logout` endpoint.

## Project Structure
- `app/`: FastAPI application source code
  - `models/`: SQLAlchemy database models
  - `routes/`: API endpoint definitions
  - `services/`: Business logic (Payments, Emails, etc.)
  - `schemas/`: Pydantic models for validation
- `Client/`: React frontend source code
- `alembic/`: Database migration history
- `tests/`: Backend test suite
- `scripts/`: Utility scripts (e.g., seeding admin users)
- `security-hardening` branch: Active branch for security and validation improvements.

## Identified States & Observations
### Database Migrations
- The project uses Alembic for schema versioning.
- **Observation:** There appear to be two separate migrations for OAuth fields (`7f6d8c9b2a31_added_oauth_fields.py` and `c336a94c7dfe_add_oauth_fields.py`). These should be verified for redundancy or sequence.

### Security & Configuration
- Secure configuration via environment variables.
- Admin access is protected by a separate secret key and role-based checks.
- Rate limiting is active and tested for Login and Booking endpoints.

### Testing State
- Backend tests are present in `tests/`.
- **Status:** Rate limit tests pass (35 tests).
- **Missing:** Comprehensive unit tests for services (Payments, Emails) and integration tests for all routes.

## Known Issues & Potential Bugs
1. **OAuth Redirects:** The OAuth flow relies on `BACKEND_BASE_URL` and `OAUTH_FRONTEND_REDIRECT_URL` settings. Ensure these are correctly configured for production.
2. **Missing Frontend Tests:** While `package.json` mentions testing tools, no frontend tests were immediately visible in the root or `Client/src` during the initial scan (beyond mentions in README).
3. **Redundant Logic:** `main.py` in the root simply imports from `app.main`, which might be redundant depending on the deployment strategy.

## Future Enhancements
- [ ] Implement End-to-End (E2E) tests.
- [ ] Expand test coverage for business logic services.
- [ ] Add more OAuth providers (e.g., LinkedIn, Microsoft).
- [ ] Implement advanced analytics dashboard for admins.

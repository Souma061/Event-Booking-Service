# Event Booking Service

## WHY
Provide a secure, high-performance platform for event discovery, ticket booking, and event management.

## WHAT
A full-stack application consisting of a FastAPI backend (PostgreSQL, SQLAlchemy, Redis) and a React 19 + TypeScript frontend (Vite, TailwindCSS) located in the `Client/` directory.

## HOW
- **Finding Information:**
  - Setup, run commands, API endpoints, and environment variables: See `README.md`.
  - Project architecture, current status, and known issues: See `PROJECT_SUMMARY.md`.
  - Security policies and improvements: See `SECURITY_ENHANCEMENTS.md`.
- **Testing & Scripts:**
  - Backend: `pytest` (tests located in `tests/`).
  - Frontend: `npm run test` in `Client/` (uses Vitest).
  - Load tests: See instructions in `README.md` and scripts in `scripts/`.
- **Database Migrations:** Managed with Alembic (see `alembic/`).
- **Code Style:** Follow existing patterns in the codebase. Rely on project linters/formatters for syntax corrections; do not act as a linter.

## Editing Guidelines
**What to Change:**
- **Frontend & UI:** Iterate freely on React components and styles in `Client/src/`.
- **New Features & Endpoints:** Safe to add new services and routes in `app/routes/` (ensure proper rate limits and auth are applied).
- **Testing:** Expanding test coverage in the `tests/` directory is highly encouraged.

**What NOT to Change:**
- **Database Schema:** Never modify SQLAlchemy models without creating a corresponding Alembic migration.
- **Security & Auth Core:** Do not alter JWT logic, OAuth flows, or security middleware (`app/middleware/`) unless specifically requested.
- **Rate Limiting:** The Valkey/Redis rate limiter parameters have been tuned for performance; do not modify limits blindly.
- **Third-Party Webhooks:** Avoid changing payment gateway (e.g., Cashfree) webhook handling without verifying exact provider payload requirements.


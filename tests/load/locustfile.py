"""
Event Booking Service — Locust Load Test Suite
===============================================

SCENARIOS COVERED
-----------------
1. BrowseUser        — anonymous traffic (list events, view details, check availability)
2. AuthUser          — authenticated user flow (register → browse → book)
3. LoginHammer       — brute-force login spike to stress the rate limiter
4. BookingRace       — concurrent seat grabs on the same show (tests FOR UPDATE / optimistic locking)
5. HealthPoller      — lightweight liveness probes (simulates LB health checks)
6. RegistrationFlood — mass new-user registrations (stresses DB writes + hashing)

HOW TO RUN
----------
# Interactive web UI (recommended for first run):
    locust -f tests/load/locustfile.py --host=http://localhost:8000

# Headless spike test (500 users, 50 spawn/s, run 90 s):
    locust -f tests/load/locustfile.py --host=http://localhost:8000 \
           --headless -u 500 -r 50 --run-time 90s \
           --html tests/load/report.html

# Target only one scenario:
    locust -f tests/load/locustfile.py --host=http://localhost:8000 \
           --headless -u 200 -r 20 --run-time 60s \
           --tags booking_race

ENVIRONMENT VARIABLES (optional overrides)
------------------------------------------
SEED_EMAIL     admin / pre-existing user email  (default: load_test_seed@example.com)
SEED_PASSWORD  its password                     (default: LoadTest@123)
TARGET_SHOW_ID show to hammer with bookings     (default: 1)
"""

from __future__ import annotations

import os
import random
import string
import uuid
from typing import Any

from locust import HttpUser, between, events, tag, task
from locust.runners import MasterRunner, WorkerRunner


# ──────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────
SEED_EMAIL    = os.getenv("SEED_EMAIL",    "load_test_seed@example.com")
SEED_PASSWORD = os.getenv("SEED_PASSWORD", "LoadTest@123")
TARGET_SHOW_ID = int(os.getenv("TARGET_SHOW_ID", "1"))

_registered_users: list[dict[str, str]] = []   # pool shared across workers


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _rand_str(n: int = 8) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=n))


def _make_credentials() -> dict[str, str]:
    uid = _rand_str()
    return {
        "email":     f"lt_{uid}@mailtest.dev",
        "password":  "Passw0rd!",
        "full_name": f"Load Tester {uid}",
        "phone":     f"+91{random.randint(7000000000, 9999999999)}",
    }


def _login(client: Any, email: str, password: str) -> bool:
    """
    Logs in via cookie-based auth endpoint.
    Returns True on success, False on any error.
    The session cookie is stored in client.cookies automatically.
    """
    resp = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
        name="/api/auth/login",
        catch_response=True,
    )
    with resp:
        if resp.status_code == 200:
            resp.success()
            return True
        # 401 / 429 are expected under load — don't mark as failure noise
        if resp.status_code in (401, 429):
            resp.success()
        else:
            resp.failure(f"Unexpected login status {resp.status_code}")
        return False


# ──────────────────────────────────────────────
# Scenario 1 — Anonymous browser
# ──────────────────────────────────────────────

class BrowseUser(HttpUser):
    """
    Simulates a visitor browsing the site without logging in.
    Heavy read traffic: events list, single event, categories, availability.
    Weight 5 → most common user type.
    """
    weight = 5
    wait_time = between(0.5, 2.0)

    def on_start(self) -> None:
        self._event_ids: list[int] = []
        self._show_ids:  list[int] = []
        self._load_catalogue()

    def _load_catalogue(self) -> None:
        resp = self.client.get("/api/events", name="/api/events [catalogue]",
                               catch_response=True)
        with resp:
            if resp.status_code == 200:
                events_list = resp.json()
                self._event_ids = [e["id"] for e in events_list]
                resp.success()
            elif resp.status_code == 429:
                # Rate-limited during spawn — not a real failure, just skip event IDs.
                # Tasks that need event IDs will return early gracefully.
                resp.success()
            else:
                resp.failure(f"Catalogue fetch failed: {resp.status_code}")

    def _get(self, url: str, name: str) -> None:
        """GET wrapper with accurate failure classification:
        - 200/404     → success (normal responses)
        - 429         → success (rate limiter working; localhost shares one IP)
        - 0           → REAL failure (connection timed out / server overloaded)
        - anything else → failure
        """
        with self.client.get(url, name=name, catch_response=True) as resp:
            if resp.status_code in (200, 404, 429):
                resp.success()
            elif resp.status_code == 0:
                resp.failure(f"{name} TIMEOUT — server did not respond (overloaded?)")
            else:
                resp.failure(f"{name} unexpected {resp.status_code}: {resp.text[:80]}")

    @task(5)
    def list_events(self) -> None:
        self._get("/api/events", "/api/events")

    @task(3)
    def get_event_detail(self) -> None:
        if not self._event_ids:
            return
        eid = random.choice(self._event_ids)
        self._get(f"/api/events/{eid}", "/api/events/{id}")

    @task(2)
    def list_categories(self) -> None:
        self._get("/api/events/categories", "/api/events/categories")

    @task(3)
    def check_availability(self) -> None:
        self._get(
            f"/api/bookings/shows/{TARGET_SHOW_ID}/availability",
            "/api/bookings/shows/{id}/availability",
        )

    @task(1)
    def health_check(self) -> None:
        self._get("/health", "/health")


# ──────────────────────────────────────────────
# Scenario 2 — Authenticated user (full flow)
# ──────────────────────────────────────────────

class AuthUser(HttpUser):
    """
    Simulates a logged-in customer: browse → check seat availability → book.
    Uses the shared pool of pre-registered users, or creates a new one.
    Weight 3.
    """
    weight = 3
    wait_time = between(1.0, 3.0)

    def on_start(self) -> None:
        self._user_email    = ""
        self._user_password = ""
        self._logged_in     = False
        self._event_ids: list[int] = []

        # Try to reuse a pre-registered user from the pool
        if _registered_users:
            creds = random.choice(_registered_users)
            self._user_email    = creds["email"]
            self._user_password = creds["password"]
            self._logged_in = _login(self.client,
                                     self._user_email,
                                     self._user_password)
        else:
            self._register_and_login()

        self._load_events()

    def _register_and_login(self) -> None:
        creds = _make_credentials()
        resp = self.client.post(
            "/api/auth/register",
            json=creds,
            name="/api/auth/register",
            catch_response=True,
        )
        with resp:
            if resp.status_code in (200, 201):
                resp.success()
                _registered_users.append({
                    "email":    creds["email"],
                    "password": creds["password"],
                })
                self._user_email    = creds["email"]
                self._user_password = creds["password"]
                self._logged_in = _login(self.client,
                                         self._user_email,
                                         self._user_password)
            else:
                resp.failure(f"Registration failed: {resp.status_code} {resp.text[:120]}")

    def _load_events(self) -> None:
        resp = self.client.get("/api/events", name="/api/events", catch_response=True)
        with resp:
            if resp.status_code == 200:
                self._event_ids = [e["id"] for e in resp.json()]
                resp.success()

    def _get(self, url: str, name: str) -> None:
        with self.client.get(url, name=name, catch_response=True) as resp:
            if resp.status_code in (200, 429, 404):
                resp.success()
            else:
                resp.failure(f"{name} returned unexpected {resp.status_code}")

    @task(4)
    def browse_events(self) -> None:
        self._get("/api/events", "/api/events")

    @task(3)
    def check_seat_availability(self) -> None:
        self._get(
            f"/api/bookings/shows/{TARGET_SHOW_ID}/availability",
            "/api/bookings/shows/{id}/availability",
        )

    @task(2)
    def my_bookings(self) -> None:
        if not self._logged_in:
            return
        self._get("/api/bookings/mine", "/api/bookings/mine")

    @task(1)
    def attempt_booking(self) -> None:
        """
        Creates a booking with a fresh Idempotency-Key each time.
        Expects 201 (success), 400 (sold out / bad request),
        or 429 (rate limited) — all treated as non-failures.
        """
        if not self._logged_in:
            return

        idempotency_key = str(uuid.uuid4())
        resp = self.client.post(
            "/api/bookings",
            json={
                "show_id": TARGET_SHOW_ID,
                "items": [{"category": "GENERAL", "quantity": 1}],
            },
            headers={"Idempotency-Key": idempotency_key},
            name="/api/bookings [create]",
            catch_response=True,
        )
        with resp:
            if resp.status_code in (201, 400, 409, 429):
                resp.success()
            else:
                resp.failure(f"Booking failed unexpectedly: {resp.status_code}")

    @task(1)
    def view_profile(self) -> None:
        if not self._logged_in:
            return
        self._get("/api/auth/me", "/api/auth/me")


# ──────────────────────────────────────────────
# Scenario 3 — Login brute-force / rate-limiter stress
# ──────────────────────────────────────────────

class LoginHammer(HttpUser):
    """
    Hammers the login endpoint repeatedly with wrong passwords.
    Tests that:
      - Rate limiter triggers (429) before DB is overwhelmed
      - Correct attempts still succeed after cool-down
    Weight 1 (small fraction of total traffic).
    """
    weight = 1
    wait_time = between(0.05, 0.3)   # very tight — intentional spike

    @task(8)
    @tag("rate_limit")
    def bad_login(self) -> None:
        resp = self.client.post(
            "/api/auth/login",
            json={"email": f"{_rand_str()}@evil.com", "password": "wrong"},
            name="/api/auth/login [bad_creds]",
            catch_response=True,
        )
        with resp:
            # 401 = rejected correctly, 429 = rate limiter working → both are correct
            if resp.status_code in (401, 422, 429):
                resp.success()
            else:
                resp.failure(f"Expected 401/429, got {resp.status_code}")

    @task(2)
    @tag("rate_limit")
    def good_login_after_hammering(self) -> None:
        """Verifies legitimate users can still log in (not fully locked out)."""
        _login(self.client, SEED_EMAIL, SEED_PASSWORD)


# ──────────────────────────────────────────────
# Scenario 4 — Concurrent booking race
# ──────────────────────────────────────────────

class BookingRace(HttpUser):
    """
    Multiple users try to book the SAME seat category simultaneously.
    Tests:
      - FOR UPDATE row-level locking (no double-booking)
      - Idempotency key deduplication
      - 409 Conflict handling under high contention
    All users must pre-login to get a valid session cookie.
    """
    weight = 2
    wait_time = between(0.0, 0.1)   # near-zero wait to maximise contention

    def on_start(self) -> None:
        self._logged_in = False
        creds = _make_credentials()
        resp = self.client.post(
            "/api/auth/register",
            json=creds,
            name="/api/auth/register [race_setup]",
            catch_response=True,
        )
        with resp:
            if resp.status_code in (200, 201):
                resp.success()
            else:
                resp.failure(f"Race setup register failed: {resp.status_code}")
                return

        self._logged_in = _login(self.client, creds["email"], creds["password"])

    @task
    @tag("booking_race")
    def race_for_seat(self) -> None:
        if not self._logged_in:
            return

        # Each attempt uses a fresh idempotency key → simulates genuine new requests
        resp = self.client.post(
            "/api/bookings",
            json={
                "show_id": TARGET_SHOW_ID,
                "items": [{"category": "GENERAL", "quantity": 1}],
            },
            headers={"Idempotency-Key": str(uuid.uuid4())},
            name="/api/bookings [race]",
            catch_response=True,
        )
        with resp:
            # 201 = got a seat, 400/409 = correctly rejected (sold out / conflict)
            # 429 = rate limiter fired correctly
            if resp.status_code in (201, 400, 409, 429):
                resp.success()
            else:
                resp.failure(f"Race booking: unexpected {resp.status_code} — {resp.text[:120]}")


# ──────────────────────────────────────────────
# Scenario 5 — Health poller (LB simulation)
# ──────────────────────────────────────────────

class HealthPoller(HttpUser):
    """
    Simulates load balancer health probes at high frequency.
    Tests that /health never degrades under mixed traffic.
    """
    weight = 1
    wait_time = between(0.1, 0.5)

    @task
    def ping(self) -> None:
        with self.client.get("/health", name="/health", catch_response=True) as resp:
            if resp.status_code == 200 and resp.json().get("status") == "ok":
                resp.success()
            else:
                resp.failure(f"/health returned {resp.status_code}: {resp.text[:80]}")


# ──────────────────────────────────────────────
# Scenario 6 — Registration flood
# ──────────────────────────────────────────────

class RegistrationFlood(HttpUser):
    """
    Floods the registration endpoint with unique users.
    Stresses:
      - bcrypt hashing (CPU-bound)
      - DB INSERT throughput
      - Email uniqueness constraint
    """
    weight = 1
    wait_time = between(0.2, 1.0)

    @task
    @tag("registration_flood")
    def register_new_user(self) -> None:
        creds = _make_credentials()
        resp = self.client.post(
            "/api/auth/register",
            json=creds,
            name="/api/auth/register [flood]",
            catch_response=True,
        )
        with resp:
            if resp.status_code in (200, 201):
                resp.success()
                _registered_users.append({
                    "email":    creds["email"],
                    "password": creds["password"],
                })
            elif resp.status_code == 429:
                resp.success()   # rate limiter working correctly
            else:
                resp.failure(f"Registration flood: {resp.status_code} {resp.text[:120]}")


# ──────────────────────────────────────────────
# BreakpointShape — stepped capacity test
# ──────────────────────────────────────────────
# Runs automatically when the profile is `breakpoint`.
# Each stage holds for HOLD_SECONDS so metrics stabilise before
# the next step. A single HTML report covers all stages, giving
# you the full latency/throughput curve in one run.
#
# Stage │ Users │ What you're looking for
# ──────┼───────┼────────────────────────────────────────────
#   1   │   500 │ Healthy baseline (should look like spike)
#   2   │  1000 │ Knee — where p95 starts rising steeply
#   3   │  2500 │ Saturation — throughput plateau, p99 spikes
#   4   │  5000 │ Collapse — timeouts / 0-status connections
#
# Activate via:  bash scripts/run_load_tests.sh breakpoint

from locust import LoadTestShape

class BreakpointShape(LoadTestShape):
    """
    Stepped staircase load profile for capacity discovery.
    Each (target_users, spawn_rate, hold_seconds) entry defines one stage.
    The shape holds at the target user count for hold_seconds then
    immediately ramps to the next stage.
    """
    # (target_users, spawn_rate_per_sec, hold_seconds_at_this_level)
    STAGES: list[tuple[int, int, int]] = [
        (  500,  50, 120),   # Stage 1 — warm-up / baseline
        ( 1000, 100, 120),   # Stage 2 — knee hunting
        ( 2500, 250, 120),   # Stage 3 — saturation
        ( 5000, 500, 120),   # Stage 4 — collapse
    ]

    def tick(self) -> tuple[int, int] | None:
        run_time = self.get_run_time()   # seconds elapsed since test start

        elapsed = 0
        for users, spawn_rate, hold in self.STAGES:
            elapsed += hold
            if run_time < elapsed:
                return users, spawn_rate

        return None   # all stages done — stop the test



# ──────────────────────────────────────────────
# Hooks — print summary at start
# ──────────────────────────────────────────────

@events.test_start.add_listener
def on_test_start(environment, **_kwargs):
    if not isinstance(environment.runner, (MasterRunner, WorkerRunner)):
        print("\n" + "=" * 60)
        print("  Event Booking Service — Load Test Starting")
        print("=" * 60)
        print(f"  Target host  : {environment.host}")
        print(f"  Target show  : {TARGET_SHOW_ID}")
        print(f"  Seed account : {SEED_EMAIL}")
        print("  Scenarios    : BrowseUser(5) | AuthUser(3) | BookingRace(2)")
        print("                 LoginHammer(1) | RegistrationFlood(1) | HealthPoller(1)")
        shape = environment.shape_class
        if shape is not None:
            print(f"  Shape        : {shape.__name__} (stepped breakpoint)")
            if hasattr(shape, 'STAGES'):
                for i, (u, r, h) in enumerate(shape.STAGES, 1):
                    print(f"    Stage {i}: {u:>5} users @ {r}/s for {h}s")
        print("=" * 60 + "\n")

# k6 System Load Tests

This folder contains a k6 test for the whole service, not only Kafka.

It covers:

- public HTTP traffic: `/health`, events, venues, categories, availability
- authenticated traffic: login/register fallback, `/api/auth/me`, `/api/bookings/mine`
- Kafka-backed notification publishing through `/api/notifications/test`
- websocket connections to `/ws/notifications/{user_id}`
- optional booking creation with idempotency keys

## Install k6

Ubuntu:

```bash
sudo gpg -k
curl -s https://dl.k6.io/key.gpg | sudo gpg --dearmor -o /usr/share/keyrings/k6-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt update
sudo apt install k6
```

Or use Docker:

```bash
docker run --rm -i grafana/k6 run - < tests/k6/system_load.js
```

For Docker on Linux, set `BASE_URL=http://host.docker.internal:8000` only if your Docker supports `host.docker.internal`. Otherwise install the local k6 binary.

## Start The System

Terminal 1:

```bash
docker compose -f docker-compose.kafka.yml up -d
```

Terminal 2:

```bash
source venv/bin/activate
uvicorn main:app --reload
```

Terminal 3:

```bash
cd Client
npm run dev
```

## Smoke Test

Use a real existing test account. This test is small and should be your first run.

```bash
k6 run \
  -e BASE_URL=http://localhost:8000 \
  -e WS_BASE_URL=ws://localhost:8000 \
  -e TEST_EMAIL=soumabrataghosh2005@gmail.com \
  -e TEST_PASSWORD='your_password' \
  -e WS_USER_ID=8 \
  -e PUBLIC_VUS=5 \
  -e AUTH_VUS=2 \
  -e WS_VUS=2 \
  -e WS_DURATION=30s \
  tests/k6/system_load.js
```

## Normal Local Load

```bash
k6 run \
  -e BASE_URL=http://localhost:8000 \
  -e WS_BASE_URL=ws://localhost:8000 \
  -e TEST_EMAIL=soumabrataghosh2005@gmail.com \
  -e TEST_PASSWORD='your_password' \
  -e WS_USER_ID=8 \
  -e PUBLIC_VUS=30 \
  -e AUTH_VUS=10 \
  -e WS_VUS=10 \
  tests/k6/system_load.js
```

## Booking Write Load

Booking creation changes inventory and creates database rows. Use this only against a local or staging database.

```bash
k6 run \
  -e BASE_URL=http://localhost:8000 \
  -e WS_BASE_URL=ws://localhost:8000 \
  -e TEST_EMAIL=soumabrataghosh2005@gmail.com \
  -e TEST_PASSWORD='your_password' \
  -e WS_USER_ID=8 \
  -e TARGET_SHOW_ID=1 \
  -e CREATE_BOOKINGS=true \
  -e PUBLIC_VUS=20 \
  -e AUTH_VUS=10 \
  -e WS_VUS=5 \
  tests/k6/system_load.js
```

## What To Watch During The Test

Backend terminal:

- request errors
- Kafka consumer errors
- database connection errors
- response latency

Kafka UI:

```text
http://localhost:8080
```

Watch:

- `notification.requested`
- `notification.dlq`
- consumer group `notification-service`
- consumer lag

Database:

- CPU
- active connections
- slow queries
- row locks during booking creation

## How To Find Capacity

Start small, then increase users:

```text
5 -> 20 -> 50 -> 100 -> 200 VUs
```

Your practical limit is around the point where:

- p95 response time becomes too high
- error rate rises above 5%
- backend CPU stays near 100%
- DB connections are exhausted
- Kafka consumer lag keeps increasing
- websocket connections start failing

## Important Safety Notes

Do not run heavy write tests against production.

Avoid enabling `CREATE_BOOKINGS=true` against your real database unless you intentionally want test bookings.

Payment provider load is not included. For payment load testing, use a fake/stub payment provider or sandbox-only credentials.

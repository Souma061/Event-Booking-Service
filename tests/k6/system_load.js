import http from 'k6/http';
import ws from 'k6/ws';
import { check, group, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';
import exec from 'k6/execution';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const WS_BASE_URL = __ENV.WS_BASE_URL || BASE_URL.replace(/^http/, 'ws');
const TEST_EMAIL = __ENV.TEST_EMAIL || '';
const TEST_PASSWORD = __ENV.TEST_PASSWORD || '';
const TARGET_SHOW_ID = Number(__ENV.TARGET_SHOW_ID || '1');
const CREATE_BOOKINGS = (__ENV.CREATE_BOOKINGS || 'false').toLowerCase() === 'true';
const RUN_NOTIFICATIONS = (__ENV.RUN_NOTIFICATIONS || 'true').toLowerCase() === 'true';

const bookingAttempts = new Counter('booking_attempts');
const notificationAttempts = new Counter('notification_attempts');
const websocketMessages = new Counter('websocket_messages_received');
const authFailures = new Rate('auth_failures');
const notificationFailures = new Rate('notification_failures');
const websocketConnectTime = new Trend('websocket_connect_time');

export const options = {
  scenarios: {
    public_api: {
      executor: 'ramping-vus',
      exec: 'publicApiScenario',
      stages: [
        { duration: '30s', target: Number(__ENV.PUBLIC_VUS || '20') },
        { duration: '1m', target: Number(__ENV.PUBLIC_VUS || '20') },
        { duration: '30s', target: 0 },
      ],
    },
    authenticated_api: {
      executor: 'ramping-vus',
      exec: 'authenticatedScenario',
      startTime: '5s',
      stages: [
        { duration: '30s', target: Number(__ENV.AUTH_VUS || '10') },
        { duration: '1m', target: Number(__ENV.AUTH_VUS || '10') },
        { duration: '30s', target: 0 },
      ],
    },
    websocket_users: {
      executor: 'constant-vus',
      exec: 'websocketScenario',
      vus: Number(__ENV.WS_VUS || '5'),
      duration: __ENV.WS_DURATION || '2m',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.05'],
    http_req_duration: ['p(95)<1200', 'p(99)<2500'],
    checks: ['rate>0.95'],
    auth_failures: ['rate<0.05'],
    notification_failures: ['rate<0.05'],
    websocket_connect_time: ['p(95)<1000'],
  },
};

function uniqueEmail() {
  return `k6_${Date.now()}_${exec.vu.idInTest}_${Math.floor(Math.random() * 100000)}@loadtest.dev`;
}

function login() {
  if (!TEST_EMAIL || !TEST_PASSWORD) {
    return false;
  }

  const res = http.post(
    `${BASE_URL}/api/auth/login`,
    JSON.stringify({ email: TEST_EMAIL, password: TEST_PASSWORD }),
    { headers: { 'Content-Type': 'application/json' }, tags: { name: 'POST /api/auth/login' } },
  );

  const ok = check(res, {
    'login status is 200': (r) => r.status === 200,
  });
  authFailures.add(!ok);
  return ok;
}

function registerAndLogin() {
  const email = uniqueEmail();
  const password = 'Passw0rd!';

  const registerRes = http.post(
    `${BASE_URL}/api/auth/register`,
    JSON.stringify({
      full_name: `K6 User ${exec.vu.idInTest}`,
      email,
      phone: `9${Math.floor(100000000 + Math.random() * 899999999)}`,
      password,
    }),
    { headers: { 'Content-Type': 'application/json' }, tags: { name: 'POST /api/auth/register' } },
  );

  const registered = check(registerRes, {
    'register status is 201': (r) => r.status === 201,
  });

  if (!registered) {
    authFailures.add(true);
    return false;
  }

  const loginRes = http.post(
    `${BASE_URL}/api/auth/login`,
    JSON.stringify({ email, password }),
    { headers: { 'Content-Type': 'application/json' }, tags: { name: 'POST /api/auth/login' } },
  );

  const loggedIn = check(loginRes, {
    'new user login status is 200': (r) => r.status === 200,
  });
  authFailures.add(!loggedIn);
  return loggedIn;
}

function ensureLoggedIn() {
  return login() || registerAndLogin();
}

function firstAvailableInventory() {
  const res = http.get(
    `${BASE_URL}/api/bookings/shows/${TARGET_SHOW_ID}/availability`,
    { tags: { name: 'GET /api/bookings/shows/:id/availability' } },
  );

  const ok = check(res, {
    'availability status is 200 or 404': (r) => r.status === 200 || r.status === 404,
  });

  if (!ok || res.status !== 200) {
    return null;
  }

  const body = res.json();
  const rows = body.inventory || [];
  return rows.find((row) => row.available_seats > 0) || null;
}

export function publicApiScenario() {
  group('public browsing', () => {
    check(http.get(`${BASE_URL}/health`, { tags: { name: 'GET /health' } }), {
      'health is 200': (r) => r.status === 200,
    });

    const eventsRes = http.get(`${BASE_URL}/api/events`, { tags: { name: 'GET /api/events' } });
    check(eventsRes, {
      'events status is 200': (r) => r.status === 200,
    });

    http.get(`${BASE_URL}/api/events/categories`, { tags: { name: 'GET /api/events/categories' } });
    http.get(`${BASE_URL}/api/events/venues`, { tags: { name: 'GET /api/events/venues' } });
    http.get(
      `${BASE_URL}/api/bookings/shows/${TARGET_SHOW_ID}/availability`,
      { tags: { name: 'GET /api/bookings/shows/:id/availability' } },
    );
  });

  sleep(Math.random() * 2 + 0.5);
}

export function authenticatedScenario() {
  if (!ensureLoggedIn()) {
    sleep(1);
    return;
  }

  group('authenticated browsing', () => {
    check(http.get(`${BASE_URL}/api/auth/me`, { tags: { name: 'GET /api/auth/me' } }), {
      'me status is 200': (r) => r.status === 200,
    });

    http.get(`${BASE_URL}/api/bookings/mine`, { tags: { name: 'GET /api/bookings/mine' } });

    if (RUN_NOTIFICATIONS) {
      notificationAttempts.add(1);
      const notificationRes = http.post(
        `${BASE_URL}/api/notifications/test`,
        null,
        { tags: { name: 'POST /api/notifications/test' } },
      );
      const ok = check(notificationRes, {
        'notification test status is 200': (r) => r.status === 200,
        'notification published': (r) => r.status === 200 && r.json('published') === true,
      });
      notificationFailures.add(!ok);
    }
  });

  if (CREATE_BOOKINGS) {
    group('optional booking creation', () => {
      const inventory = firstAvailableInventory();
      if (!inventory) {
        return;
      }

      bookingAttempts.add(1);
      const res = http.post(
        `${BASE_URL}/api/bookings`,
        JSON.stringify({
          show_id: TARGET_SHOW_ID,
          items: [{ category: inventory.category, quantity: 1 }],
        }),
        {
          headers: {
            'Content-Type': 'application/json',
            'Idempotency-Key': `k6-${exec.vu.idInTest}-${Date.now()}-${Math.random()}`,
          },
          tags: { name: 'POST /api/bookings' },
        },
      );

      check(res, {
        'booking status is expected': (r) => [201, 400, 409, 429].includes(r.status),
      });
    });
  }

  sleep(Math.random() * 3 + 1);
}

export function websocketScenario() {
  const userId = __ENV.WS_USER_ID || '8';
  const started = Date.now();
  const res = ws.connect(`${WS_BASE_URL}/ws/notifications/${userId}`, {}, (socket) => {
    socket.on('open', () => {
      websocketConnectTime.add(Date.now() - started);
      socket.setInterval(() => {
        socket.send('ping');
      }, 5000);
    });

    socket.on('message', () => {
      websocketMessages.add(1);
    });

    socket.setTimeout(() => {
      socket.close();
    }, Number(__ENV.WS_HOLD_MS || '30000'));
  });

  check(res, {
    'websocket status is 101': (r) => r && r.status === 101,
  });
}

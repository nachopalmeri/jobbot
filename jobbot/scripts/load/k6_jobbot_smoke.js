import http from "k6/http";
import { check, group, sleep } from "k6";

const API_BASE = __ENV.API_BASE || "http://127.0.0.1:8000";
const PASSWORD = __ENV.LOAD_TEST_PASSWORD || "LoadTest123!";
const EMAIL_PREFIX = __ENV.LOAD_TEST_EMAIL_PREFIX || "loadtest";

export const options = {
  scenarios: {
    auth_and_dashboard: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "30s", target: 10 },
        { duration: "1m", target: 25 },
        { duration: "30s", target: 0 },
      ],
      gracefulRampDown: "15s",
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.02"],
    http_req_duration: ["p(95)<1200"],
    "checks{type:auth}": ["rate>0.95"],
    "checks{type:dashboard}": ["rate>0.95"],
  },
};

function jsonPost(url, payload, params = {}) {
  return http.post(url, JSON.stringify(payload), {
    headers: { "Content-Type": "application/json", ...(params.headers || {}) },
    tags: params.tags,
  });
}

export default function () {
  const unique = `${__VU}_${__ITER}_${Date.now()}`;
  const email = `${EMAIL_PREFIX}_${unique}@example.com`;

  let token = "";

  group("register_or_login", function () {
    const registerRes = jsonPost(`${API_BASE}/auth/register`, {
      email,
      password: PASSWORD,
      name: `Load User ${__VU}`,
    }, { tags: { type: "auth", endpoint: "register" } });

    if (registerRes.status === 200) {
      const body = registerRes.json();
      token = body.access_token || "";
      check(registerRes, {
        "register returns token": () => !!token,
      }, { type: "auth" });
      return;
    }

    const loginRes = http.post(
      `${API_BASE}/auth/token`,
      `username=${encodeURIComponent(email)}&password=${encodeURIComponent(PASSWORD)}`,
      {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        tags: { type: "auth", endpoint: "token" },
      },
    );

    if (loginRes.status === 200) {
      const body = loginRes.json();
      token = body.access_token || "";
    }

    check(loginRes, {
      "auth endpoint is healthy": (r) => [200, 401, 409, 429].includes(r.status),
    }, { type: "auth" });
  });

  if (!token) {
    sleep(0.2);
    return;
  }

  group("dashboard_reads", function () {
    const headers = { Authorization: `Bearer ${token}` };
    const dashboardRes = http.get(`${API_BASE}/users/dashboard`, {
      headers,
      tags: { type: "dashboard", endpoint: "users_dashboard" },
    });
    check(dashboardRes, {
      "dashboard status 200": (r) => r.status === 200,
      "dashboard has motivation": (r) => {
        const body = r.json();
        return !!body.daily_motivation;
      },
    }, { type: "dashboard" });

    const previewRes = http.get(`${API_BASE}/jobs/dashboard-preview`, {
      headers,
      tags: { type: "dashboard", endpoint: "jobs_preview" },
    });
    check(previewRes, {
      "jobs preview stable": (r) => [200, 403].includes(r.status),
    }, { type: "dashboard" });
  });

  sleep(0.5);
}

# JobBot - Go Live Master Checklist

Owner: Main integrator  
Status date: 2026-04-07

## 0) Scope Lock (must be true before release)
- [x] Landing/index is the visual source of truth.
- [x] Flow is web-first, Telegram connected but not mandatory for first login.
- [x] Promised features are real (no fake UI states).
- [x] Premium promises match API and bot enforcement.

## 1) User Flow Acceptance (new real user)
- [x] Register from web works with a fresh email.
- [x] Login works and enters dashboard without loop.
- [x] Dashboard loads real payload (not permanent skeleton).
- [x] Config changes persist and do not clear session.
- [x] CV upload succeeds and updates `cv_insights`.
- [x] Dashboard shows: rating/insights, coaching tips, daily motivation, streak, weekly goal/remaining.
- [x] Jobs preview/matches are visible (or explicit empty state with guidance).
- [x] Subscription page reflects current plan and gating state.
- [x] Telegram link code generation works.
- [x] Telegram linking resolves to the same account and dashboard reflects connected status.

## 2) API Contract Acceptance
- [x] `GET /health` -> 200.
- [x] `POST /auth/register` -> account + token.
- [x] `POST /auth/token` -> token with valid credentials.
- [x] `GET /users/dashboard` -> complete payload (motivation, tips, streak, weekly, cv insights).
- [x] `POST /cv/upload` -> accepted file + dashboard updated.
- [x] `GET /jobs/dashboard-preview` -> stable response contract.
- [x] Premium endpoints return `403` for non-entitled users.

## 3) Security & Resilience
- [x] Rate-limit headers present (`X-RateLimit-*`, `Retry-After` when blocked).
- [x] 429 responses include CORS headers for browser behavior.
- [ ] `RATE_LIMIT_BACKEND=redis` path verified in staging/prod.
- [x] Session handling does not log users out on transient network errors.
- [x] No connection leak warnings in DB tests.

## 4) Performance & DB
- [x] Dashboard hot path uses bounded queries and indexes.
- [x] Applications/funnel queries indexed and stable under load.
- [x] Load smoke run attached (success rate + status summary + latency).

## 5) Visual/UX Quality
- [x] No mojibake/corrupted encoding in landing/auth/dashboard text.
- [x] Login/register/dashboard use coherent design language.
- [x] Empty/error/loading states are clear and actionable.
- [x] Mobile and desktop sanity checks pass.

## 6) Deployment Readiness
- [ ] Production env vars complete (`LANDING_URL`, `CORS_ORIGINS`, JWT, bot vars, Redis vars).
- [ ] Domain and DNS live (`jobbot.ar` + www if used).
- [ ] SSL active and redirects configured.
- [ ] Release notes prepared.
- [ ] Rollback plan documented.

## 7) Go/No-Go
- [ ] All critical items above are green.
- [ ] No unresolved P0/P1 bugs.
- [ ] Final sign-off approved.

## 8) Release Gate Evidence

Date: 2026-04-07

### PASS
- `python scripts/load/acceptance_smoke.py --base-url http://127.0.0.1:8000`
  - 13/13 checks passed.
  - Notable PASS items: register, login, dashboard load, config persistence, CV upload, matches preview, subscription gating, Telegram code generation, Telegram linking.
- `python scripts/load/python_load_smoke.py --base-url http://127.0.0.1:8000 --users 20 --iterations 2`
  - `total_requests=40`, `ok=40`, `failed=0`, `success_rate=100.0`.
  - `status_summary`: `dashboard_200=25`, `dashboard_429=15`, `jobs_200=18`, `jobs_429=22`.
- `curl.exe -i http://127.0.0.1:8000/health`
  - HTTP `200`.
  - Response body: `{"status":"ok","checks":{"database":"ok","stripe":"missing","mercadopago":"missing","groq":"configured"}}`.
- `python -m pytest -c pytest.ini api\\tests\\test_security.py -k "rate_limit or Retry-After or exempt" -q`
  - `11 passed, 44 deselected`.
- Live rate-limit burst against `POST /auth/token`
  - Attempts 1-4 returned `401`, attempts 5-6 returned `429`.
  - Headers on the blocked response included `X-RateLimit-Limit: 5`, `X-RateLimit-Remaining: 0`, and `Retry-After: 6`.

### FAIL
- `curl.exe -i http://127.0.0.1:8000/health/live`
  - HTTP `404 Not Found`.
- `curl.exe -i http://127.0.0.1:8000/health/ready`
  - HTTP `404 Not Found`.
- `python -m pytest -c pytest.ini api\\tests\\test_health.py -q`
  - Fails during import with `ModuleNotFoundError: No module named 'jobbot'`.

### Release Blockers
- The documented Kubernetes-style probe paths (`/health/live` and `/health/ready`) are not mounted by the live API.
- The health test module is wired to `jobbot.api.*`, but the repo currently exposes the API under `api.*`, so the suite cannot execute as written.

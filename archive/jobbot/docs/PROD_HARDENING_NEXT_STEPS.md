# JobBot - Next Hardening Steps

## 1) Connection Leaks
- Legacy DB tests must always close DB handles (`db.close()` in teardown).
- Keep using file-based sqlite in API tests to avoid thread-bound `:memory:` issues.
- Goal: no `ResourceWarning: unclosed database` in CI.

## 2) Load Test (k6)
- Script: `scripts/load/k6_jobbot_smoke.js`
- Run:
```bash
k6 run scripts/load/k6_jobbot_smoke.js
```
- With custom API:
```bash
API_BASE=http://127.0.0.1:8000 k6 run scripts/load/k6_jobbot_smoke.js
```
- What it stresses:
  - register/login path
  - `/users/dashboard`
  - `/jobs/dashboard-preview`

## 2.1) Load Test (Python fallback)
- Script: `scripts/load/python_load_smoke.py`
- Run:
```bash
python scripts/load/python_load_smoke.py --base-url http://127.0.0.1:8000 --users 10 --iterations 2 --seed-email <existing_email> --password <password>
```
- Output includes:
  - overall success rate
  - `status_summary` (`dashboard_200`, `dashboard_429`, `jobs_429`, etc.)
- Note: `429` can be expected when stress-testing with strict limits enabled.

## 3) DB Bottleneck Review
- Run targeted `EXPLAIN QUERY PLAN` on hottest reads:
  - dashboard payload queries
  - jobs preview queries
  - applications/funnel aggregations
- Ensure indexes exist for:
  - `applications(telegram_id, applied_at)`
  - `jobs_seen(telegram_id, seen_at)`
  - link/login code tables by `code` and `expires_at`

## 4) Rate Limit at Scale (multi-instance)
- Current limiter is in-memory, per-process.
- For horizontal scaling, move counters to Redis:
  - key format: `rl:{category}:{identity}`
  - atomic increment + TTL per window
  - preserve `Retry-After` and `X-RateLimit-*` headers
- Implemented runtime switch:
  - `RATE_LIMIT_BACKEND=memory` (default)
  - `RATE_LIMIT_BACKEND=redis` + `REDIS_URL=redis://...`
  - If Redis is unavailable, fallback to memory limiter

## 5) Production Gate
- Required before public deploy:
  - `next build` green
  - API security/rate-limit tests green
  - k6 smoke within thresholds
  - no connection warnings in test logs

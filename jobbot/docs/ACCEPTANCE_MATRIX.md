# JobBot Acceptance Matrix

Date: 2026-04-07

## Scope
New-user end-to-end validation for:
- register/login
- dashboard load
- config persistence
- CV upload + insights
- matches preview
- tips / motivation / streak / weekly goal
- subscription gating
- Telegram code generation / linking

## Matrix

| Area | Status | Evidence | Exact repro |
| --- | --- | --- | --- |
| Health check | PASS | `GET /health` returned `200` | `curl -i http://127.0.0.1:8000/health` |
| Register | PASS | New web account created and token returned | `curl -i -X POST http://127.0.0.1:8000/auth/register -H "Content-Type: application/json" -d "{\"email\":\"...\",\"password\":\"...\",\"name\":\"...\"}"` |
| Login | PASS | `POST /auth/token` returned `200` and access token | `curl -i -X POST http://127.0.0.1:8000/auth/token -H "Content-Type: application/x-www-form-urlencoded" -d "username=...&password=..."` |
| Dashboard load | PASS | Dashboard returned `daily_motivation`, `application_streak`, `weekly_goal`, `weekly_remaining`, `cv_insights`, `coaching_tips` | `curl -i http://127.0.0.1:8000/users/dashboard -H "Authorization: Bearer $TOKEN"` |
| Config persistence | PASS | Preferences persisted after `POST /users/preferences` and reloaded via `GET /users/preferences` | `curl -i -X POST http://127.0.0.1:8000/users/preferences -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "..."` then `curl -i http://127.0.0.1:8000/users/preferences -H "Authorization: Bearer $TOKEN"` |
| CV upload + insights | PASS | Upload succeeded and dashboard reflected `cv_insights.uploaded=true` with a score | `curl -i -X POST http://127.0.0.1:8000/cv/upload -H "Authorization: Bearer $TOKEN" -F "file=@cv.txt"` |
| Matches preview | PASS | `GET /jobs/dashboard-preview` returned `200` with jobs in preview payload | `curl -i http://127.0.0.1:8000/jobs/dashboard-preview -H "Authorization: Bearer $TOKEN"` |
| Tips | PASS | `GET /cv/tips/demo-job` returned 3 tips | `curl -i http://127.0.0.1:8000/cv/tips/demo-job -H "Authorization: Bearer $TOKEN"` |
| Motivation / streak / weekly goal | PASS | Dashboard reflected motivation, streak, and weekly goal fields | `curl -i http://127.0.0.1:8000/users/dashboard -H "Authorization: Bearer $TOKEN"` |
| Subscription status / plans | PASS | `GET /subscriptions/status` and `GET /subscriptions/plans` returned valid payloads | `curl -i http://127.0.0.1:8000/subscriptions/status -H "Authorization: Bearer $TOKEN"` and `curl -i http://127.0.0.1:8000/subscriptions/plans` |
| Subscription gating | PASS | Free plan was blocked with `403` on premium-only endpoints | `curl -i -X POST "http://127.0.0.1:8000/cv/mock-interview?job_title=Backend%20Developer" -H "Authorization: Bearer $TOKEN"` |
| Telegram code generation | PASS | `POST /auth/telegram/link-code` returned a code and deep link | `curl -i -X POST http://127.0.0.1:8000/auth/telegram/link-code -H "Authorization: Bearer $TOKEN"` |
| Telegram linking | PASS | Link code was consumed and account migrated to a real Telegram user id | Generate code, consume it via `job_bot.database.Database.consume_telegram_link_code()`, then call `link_web_account_to_telegram()` and reload the dashboard |

## Current release blockers

- No functional P0 blocker reproduced in latest acceptance smoke.
- Environment caveat: in restricted sandboxes, `pytest` can fail creating temp/cache dirs due filesystem permissions (not due to app logic).

## Commands run

- `python -m pytest -c pytest.ini api/tests/test_security.py -k "endpoint_rate_limiter_falls_back_when_backend_fails or endpoint_rate_limiter_uses_redis_backend_when_available or dashboard_preview_falls_back_when_search_is_unavailable" -q`
- `python scripts/load/acceptance_smoke.py --base-url http://127.0.0.1:8000`
- `python -m unittest job_bot.tests.test_database`
- `pytest -c pytest.ini api/tests/test_auth.py -k rate_limit -q`
- `npm run build` in `frontend` (latest run passed)
- `frontend/.\\node_modules\\.bin\\tsc.cmd --noEmit`

## Notes

- The acceptance smoke uses a fresh web account per run and simulates the Telegram link consumption path locally so the result is reproducible.
- Production hardening in this pass included the dashboard preview fallback, a `pending_job_batches(created_at)` index, and frontend build config changes to route TypeScript through `prebuild` plus `workerThreads`.

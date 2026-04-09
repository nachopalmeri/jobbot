# JobBot Go-Live Guide

## Required env vars
- `APP_ENV=production`
- `JWT_SECRET_KEY=<strong secret>`
- `LANDING_URL=https://jobbot.ar`
- `CORS_ORIGINS=https://jobbot.ar,https://www.jobbot.ar`
- `DATABASE_TYPE=supabase` or `DATABASE_TYPE=sqlite` for local-only
- `RATE_LIMIT_BACKEND=redis`
- `REDIS_URL=redis://<host>:6379/0`
- `TELEGRAM_BOT_TOKEN=<bot token>`
- `TELEGRAM_BOT_USERNAME=<bot username>`

## Recommended production limits
- `LOGIN_RATE_LIMIT=5`
- `REGISTER_RATE_LIMIT=3`
- `SEARCH_RATE_LIMIT=20`
- `CV_RATE_LIMIT=6`
- `TELEGRAM_RATE_LIMIT=10`
- `DASHBOARD_RATE_LIMIT=30`

## Scaling caveats
- The in-memory limiter is safe for local development only.
- For multiple API instances, Redis-backed rate limiting is required.
- If Redis fails at runtime, the current process falls back to in-memory limiting so traffic keeps flowing, but limits are no longer global across instances.
- Dashboard/application queries rely on `(telegram_id, applied_at)` and `(telegram_id, status)` indexes. Keep them in the production schema.

## Verification checklist
- `next build` passes.
- API health returns `200`.
- Rate-limit headers appear on auth and dashboard responses.
- `register -> dashboard -> CV upload -> Telegram link` works for a fresh user.
- Load smoke with 10 concurrent users stays within acceptable error rate.

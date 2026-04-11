# Legacy Assets

This folder contains files that are no longer part of the production runtime.

Current canonical stack:

- Public landing and dashboard: `frontend/`
- API: `api/`
- Telegram bot: `job_bot/`

The static HTML landing was kept only as a legacy backup because an older Vercel deployment may still point to it. Do not use these files as the source of truth for pricing, product copy, or feature availability.

Archived here:

- `static-landing/dashboard-demo.html`
- `static-landing/mockup_pro.png`
- `static-landing/package.json`
- `static-landing/rewrite_clean.py`

If you migrate Vercel fully to `frontend/`, the next cleanup step can be archiving `job_bot/landing/index.html` too.

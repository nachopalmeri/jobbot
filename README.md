# JobBot — Autopilot for Your Job Search in LATAM

JobBot es una plataforma de búsqueda laboral tech para LATAM que automatiza 90% de la búsqueda de trabajo con IA.

**Status**: Controlled launch beta — Producto funcional, 100% conectado, lista para usuarios reales.

## Superficies Activas

| Superficie | Tecnología | Estado |
|------------|------------|--------|
| `api/` | FastAPI + PostgreSQL | ✅ Producción-ready (auth, billing, jobs, CV Suite) |
| `dashboard/` | Next.js 16 App Router | ✅ Producción-ready (landing, auth, dashboard real) |
| `job_bot/` | Python Telegram Bot | ✅ Producción-ready (14 comandos, alertas, scraping) |

## Qué Funciona Hoy

### ✅ Features Productivas (Launch Ready)
- **Auth real**: JWT en cookies httpOnly, registro/login funcionando
- **Dashboard real**: Datos de PostgreSQL, 0% mock data
- **Pipeline de postulaciones**: CRUD completo, kanban view
- **Checkout funcional**: Stripe + MercadoPago + webhooks automáticos
- **Planes**: Free, Starter ($4), Pro ($8), Premium ($12)
- **CV Suite**: ATS scoring, match con ofertas, cover letters (Groq/Llama)
- **Bot Telegram**: 14 comandos, alertas programadas, Smart Summary UX
- **Landing**: Next.js SSR, SEO-optimized, CTAs reales
- **Cache**: Redis distribuido activo en endpoints críticos
- **Workers**: Celery async para scraping, notificaciones, AI
- **CI/CD**: GitHub Actions (tests, security, integration, deploy)
- **Health**: `/health/ready` para Kubernetes/ALB

### ⚠️ En Beta / Mejoras Futuras
- Analytics PostHog (tracking conversiones) - opcional pre-launch
- GDPR data export endpoint - opcional pre-launch
- NPS survey - post-launch

## Estructura Canónica

```
jobbot/
├── api/              # FastAPI: auth, billing, jobs, admin
├── dashboard/        # Next.js: landing, auth, dashboard
├── job_bot/          # Telegram bot + scrapers + scheduler
├── archive/          # Duplicados históricos (inactivos)
└── tasks/            # todo.md, lessons.md, architecture_log.md
```

**No considerar para release**: Código fuera de `api/`, `dashboard/`, `job_bot/`.

## Desarrollo Local

### Requisitos
- Python 3.11+ con virtualenv
- Node.js 18+ para dashboard
- PostgreSQL (prod) o SQLite (dev local)

### Backend API
```bash
.venv/bin/pip install -r api/requirements.txt
export APP_ENV=development
export JWT_SECRET_KEY=$(openssl rand -hex 32)
.venv/bin/uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

### Dashboard
```bash
cd dashboard
npm install
npm run dev  # http://localhost:3000
```

### Bot Telegram
```bash
.venv/bin/pip install -r job_bot/requirements.txt
cd job_bot
export TELEGRAM_TOKEN=your_token
export GROQ_API_KEY=your_key
python bot.py
```

## Seguridad

- ✅ Security score: 85/100 post hardening
- ✅ No secrets hardcodeados (C1, C2, C3 resueltos)
- ✅ Cookies httpOnly, JWT validation
- ✅ Webhooks con HMAC/signature verification
- ✅ PII excluido de git (`.gitignore` endurecido)

## Verificación Pre-Deploy

```bash
# Tests
.venv/bin/python -m pytest -q

# Build dashboard
cd dashboard && npm run build

# Verificar seguridad
grep -r "password\|secret\|token" --include="*.py" api/ | grep -v "\.pyc" | head -5

# Verificar conexiones API
curl http://localhost:8000/health
```

## Variables de Entorno Críticas

```bash
# Auth (REQUERIDO en prod)
JWT_SECRET_KEY=<min-32-chars>

# Database (REQUERIDO en prod)
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://user:pass@host/db

# Pagos (para checkout funcional)
STRIPE_SECRET_KEY=sk_...
STRIPE_WEBHOOK_SECRET=whsec_...
MP_ACCESS_TOKEN=...

# APIs
GROQ_API_KEY=gsk_...
TELEGRAM_TOKEN=...:...
```

## Documentación
- [Plan Final Implementation](.kilo/plans/1775760920752-gentle-lagoon.md)
- [Architecture Log](tasks/architecture_log.md)
- [Lessons Learned](tasks/lessons.md)

## Licencia
Private - All rights reserved

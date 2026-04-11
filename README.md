# JobBot

JobBot tiene hoy dos superficies web separadas:

- **Landing pública marketinera** en `job_bot/landing/`
- **App real / dashboard** en `dashboard/`

Eso no es un accidente: la landing vende y deriva tráfico; el dashboard es donde vive el producto autenticado.

**Status**: Controlled launch beta

## Superficies activas

| Superficie | Tecnología | Rol operativo |
|------------|------------|---------------|
| `job_bot/landing/` | HTML/CSS/JS estático | Landing pública que se publica en Vercel |
| `dashboard/` | Next.js 16 App Router | App real: auth, dashboard, billing, CV Suite |
| `api/` | FastAPI + PostgreSQL | Backend real para auth, jobs, subscriptions y admin |
| `job_bot/` | Python Telegram Bot | Canal Telegram, alertas y automatizaciones |

## Setup actual en Vercel free

- **Landing pública**: `https://jobbot-lime.vercel.app`
- **App / dashboard**: `https://app-jobbot.vercel.app`

Mientras siga el free tier, estas URLs de Vercel son la referencia operativa. No asumir dominio custom.

## Regla canónica

- La landing pública que se publica hoy sale de `job_bot/landing/`.
- El dashboard publicado sale de `dashboard/`.
- Los CTAs de la landing deben apuntar siempre a `app-jobbot.vercel.app`.
- El código legacy o duplicado fuera de `api/`, `dashboard/`, `job_bot/` y `job_bot/landing/` no entra en el camino de release.

## Qué funciona hoy

- Auth real con cookies `httpOnly`
- Dashboard conectado a la API real
- Checkout funcional con Stripe y MercadoPago
- Planes consistentes: Free, Starter ($4), Pro ($8), Premium ($12)
- Sistema de créditos para CV Suite
- Bot de Telegram con alertas, linking y flujos premium
- Health checks y CI del repo

## Estructura canónica

```text
jobbot/
├── api/              # Backend real
├── dashboard/        # App real autenticada
├── job_bot/          # Bot Telegram
│   └── landing/      # Landing pública marketinera
├── archive/          # Históricos y duplicados
└── tasks/            # Documentación de trabajo
```

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

### Landing pública
```bash
cd job_bot/landing
.venv/bin/python -m http.server 3011
# http://127.0.0.1:3011
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
- [Vercel Free Setup](VERCEL_FREE_SETUP.md)
- [Plan Final Implementation](.kilo/plans/1775760920752-gentle-lagoon.md)
- [Architecture Log](tasks/architecture_log.md)
- [Lessons Learned](tasks/lessons.md)

## Licencia
Private - All rights reserved

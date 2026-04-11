# 🚀 JobBot - Autopilot for Your Tech Career in LATAM

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/tuusuario/jobbot)
[![Tests](https://img.shields.io/badge/tests-2,810%20lines-brightgreen.svg)](./api/tests)
[![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen.svg)](./api/tests)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://python.org)
[![Next.js](https://img.shields.io/badge/next.js-16-black.svg)](https://nextjs.org)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![Deploy](https://img.shields.io/badge/deploy-Railway%20%7C%20Vercel-purple.svg)](./DEPLOYMENT.md)

**JobBot** es una plataforma SaaS que automatiza la búsqueda de empleo tech en LATAM usando IA, multi-fuente scraping y analytics en tiempo real.

**🎯 Investor Deck**: [docs/INVESTOR_DECK.pptx](./docs/INVESTOR_DECK.pptx) | **One Pager**: [docs/ONE_PAGER.md](./docs/ONE_PAGER.md)

---

## 📊 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                            │
├──────────────┬──────────────────┬───────────────────────────────┤
│  Telegram    │   Next.js        │     Mobile (Future)          │
│    Bot       │   Dashboard      │       React Native           │
└──────┬───────┴────────┬─────────┴───────────────┬───────────────┘
       │                │                         │
       │   HTTPS/WSS    │                         │
       ▼                ▼                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY (FastAPI)                     │
├─────────────────────────────────────────────────────────────────┤
│  Auth (JWT)  │  Jobs  │  CV  │  Subs  │  Webhooks  │  Health    │
└──────┬───────┴────────┴──────┴────────┴────────────┴────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                              │
├──────────────────┬──────────────────┬─────────────────────────────┤
│   SQLite (dev)   │   Supabase (prod) │   File Storage            │
│   PostgreSQL     │   PostgreSQL     │   CVs / Cache             │
└──────────────────┴──────────────────┴─────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL INTEGRATIONS                       │
├──────────────────┬──────────────────┬─────────────────────────────┤
│   AI/ML          │   Payments       │   Job Sources            │
│   Groq API       │   Stripe         │   LinkedIn, Remotive     │
│   Llama 3.3      │   MercadoPago    │   Arbeitnow, Himalayas   │
│                  │   Coinbase       │   Jobicy, RSS            │
└──────────────────┴──────────────────┴─────────────────────────────┘
```

---

## 📋 Table of Contents

- [Description](#-description)
- [Architecture](#-architecture-diagram)
- [Stack](#-stack-tecnológico)
- [Quick Start](#-quick-start-developer)
- [API Reference](#-api-reference)
- [Contributing](#-contributing)
- [Changelog](#-changelog)
- [License](#-license)

---

## 🎯 Description

JobBot combina tres componentes principales para ofrecer una experiencia completa de búsqueda laboral automatizada:

### 🐛 **Job Bot de Telegram**
Bot inteligente que monitorea ofertas de empleo en tiempo real, analiza CVs con IA (Groq/Llama 3) y envía alertas personalizadas.

### ⚡ **API REST**
Backend robusto en FastAPI con autenticación JWT, rate limiting, webhooks de pagos y sistema de audit logging.

### 🎨 **Dashboard Web**
Dashboard moderno en Next.js con 8 páginas, sistema de suscripción, dark mode y panel administrativo.

### ✨ **Features Principales**
- 🤖 **IA integrada**: Análisis de CVs con Llama 3.3 70B
- 🔒 **Seguridad enterprise**: JWT, CSP, rate limiting, audit logging
- 💳 **Pagos integrados**: Stripe, MercadoPago, Coinbase
- 📊 **Dashboard analytics**: Métricas en tiempo real
- 🌐 **Multi-fuente**: LinkedIn, Remotive, Arbeitnow, Himalayas
- 📱 **Responsive**: Mobile-first design
- 🧪 **Testing completo**: 2,810 líneas de tests

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                         CLIENTES                             │
├──────────────┬────────────────┬───────────────────────────────┤
│  Telegram    │   Dashboard    │     Mobile/Web App          │
│    Bot       │   (Next.js)    │       (Future)              │
└──────┬───────┴────────┬─────────┴───────────────┬───────────────┘
       │              │                       │
       │              │   HTTPS/WSS           │
       ▼              ▼                       ▼
┌─────────────────────────────────────────────────────────────┐
│                      API LAYER (FastAPI)                     │
├─────────────────────────────────────────────────────────────┤
│  Auth (JWT)  │  Jobs  │  CV  │  Subs  │  Webhooks  │Health │
└──────┬───────┴────────┴──────┴────────┴────────────┴────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATA LAYER                                │
├──────────────────┬──────────────────┬───────────────────────────┤
│   SQLite/Supa    │   File Storage   │   External APIs         │
│    base          │   (CVs/Cache)    │   (Groq, Stripe, etc)   │
└──────────────────┴──────────────────┴───────────────────────────┘
```

### Flujo de Datos

```
1. User → Bot/Dashboard → API
2. API → Database (SQLite/Supabase)
3. Scheduler → Scrapers → External APIs
4. Scrapers → AI Analyzer → User Alerts
5. Payments → Webhooks → API → Database
```

---

## 🛠️ Stack Tecnológico

### Backend
| Componente | Tecnología | Versión |
|------------|------------|---------|
| Framework | FastAPI | 0.109+ |
| Database | SQLite / Supabase | - |
| Auth | PyJWT | 2.8+ |
| AI | Groq API | Llama 3.3 70B |
| Testing | pytest | 8.0+ |
| Task Queue | APScheduler | 3.10+ |

### Frontend (Dashboard)
| Componente | Tecnología | Versión |
|------------|------------|---------|
| Framework | Next.js | 16.2.1 |
| Language | TypeScript | 5.x |
| Styling | Tailwind CSS | v4 |
| UI | shadcn/ui | - |
| State | Zustand | 4.5+ |
| Testing | Vitest | 1.2+ |

### Bot
| Componente | Tecnología | Versión |
|------------|------------|---------|
| Framework | python-telegram-bot | 20.x |
| Scraping | BeautifulSoup, requests | - |
| AI | Groq | - |
| Database | SQLite | - |

### Infraestructura
| Servicio | Uso |
|----------|-----|
| Docker | Containerización |
| Railway / Vercel | Deploy |
| GitHub Actions | CI/CD |
| Supabase | PostgreSQL (opcional) |

---

## 📁 Estructura del Proyecto

```
jobbot/
├── 📁 api/                     # Backend FastAPI
│   ├── main.py                 # Entry point
│   ├── models.py               # Database models
│   ├── rate_limit.py           # Rate limiting logic
│   ├── middleware/               # Security middleware
│   │   ├── audit_logger.py     # Audit logging
│   │   ├── security_headers.py # CSP & headers
│   │   └── jwt_blacklist.py    # Token blacklist
│   ├── routes/                 # API endpoints
│   │   ├── auth.py             # JWT auth & refresh
│   │   ├── users.py            # User management
│   │   ├── jobs.py             # Jobs endpoints
│   │   ├── cv.py               # CV analysis
│   │   ├── subscriptions.py    # Payments
│   │   ├── public.py           # Public endpoints
│   │   └── health.py           # Health checks
│   ├── webhooks/               # Payment webhooks
│   └── tests/                  # API tests (810 líneas)
│       ├── test_auth.py
│       ├── test_security.py
│       ├── test_webhooks.py
│       └── test_health.py
│
├── 📁 dashboard/               # Frontend Next.js
│   ├── src/
│   │   ├── app/                # Next.js App Router
│   │   │   ├── (auth)/         # Login/Register
│   │   │   └── (dashboard)/    # Dashboard pages (8)
│   │   ├── components/         # UI components (12)
│   │   ├── stores/             # Zustand state
│   │   └── lib/                # Utilities
│   ├── __tests__/              # Component tests (2000 líneas)
│   └── package.json
│
├── 📁 job_bot/                 # Telegram Bot
│   ├── bot.py                  # Bot entry point
│   ├── job_scraper.py          # Scrapers (6 fuentes)
│   ├── cv_analyzer.py          # AI analysis
│   ├── database.py             # Database layer
│   ├── backup.py               # Backup system
│   └── tests/                  # Bot tests
│
├── 📁 docs/                    # Documentación
│   └── plans/                  # Planes de desarrollo
│
├── 📁 scripts/                 # Utilidades
├── 📁 cvs/                     # CV storage
├── .env.example                # Template variables
├── CHANGELOG.md                # Historial de cambios
├── DEPLOYMENT.md               # Guía de deploy
└── README.md                   # Este archivo
```

---

## 🚀 Quick Start

### Prerrequisitos
- Python 3.11+
- Node.js 18+
- npm/pnpm
- Git

### 1. Clonar el Repositorio

```bash
git clone https://github.com/tuusuario/jobbot.git
cd jobbot
```

### 2. Configurar Backend (API)

```bash
# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements_api.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores

# Ejecutar tests
pytest api/tests/ -v

# Iniciar servidor
cd api
uvicorn main:app --reload --port 8000
```

### 3. Configurar Dashboard

```bash
cd dashboard

# Instalar dependencias
npm install

# Configurar variables de entorno
cp .env.local.example .env.local

# Ejecutar tests
npm test

# Iniciar servidor de desarrollo
npm run dev
```

### 4. Configurar Bot (Opcional)

```bash
cd job_bot

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env

# Ejecutar tests
python -m pytest tests/ -v

# Iniciar bot
python bot.py
```

### 5. Verificar Instalación

Visita:
- API Docs: `http://localhost:8000/docs`
- Dashboard: `http://localhost:3000`
- Health Check: `http://localhost:8000/health`

---

## 🔐 Variables de Entorno

### Variables Críticas (Producción)

```env
# App
APP_ENV=production
LOG_LEVEL=INFO

# JWT (¡CAMBIAR EN PRODUCCIÓN!)
JWT_SECRET_KEY=your-super-secret-key-min-32-chars

# Database
DATABASE_TYPE=sqlite  # o supabase
DATABASE_PATH=job_bot.db
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Telegram (solo para bot)
TELEGRAM_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11

# AI
GROQ_API_KEY=gsk_xxxxxxxx

# Payments
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
MP_ACCESS_TOKEN=APP_USR-...
MP_WEBHOOK_SECRET=...

# Rate Limiting
LOGIN_RATE_LIMIT=5
LOGIN_RATE_WINDOW_SECONDS=900
API_RATE_LIMIT=100
API_RATE_WINDOW_SECONDS=60
```

Ver el archivo [`.env.example`](.env.example) completo.

---

## ⌨️ Comandos Útiles

### Desarrollo

```bash
# Backend
uvicorn api.main:app --reload --port 8000
python -m pytest api/tests/ -v
python -m pytest api/tests/ --cov=api

# Dashboard
cd dashboard && npm run dev
cd dashboard && npm test
cd dashboard && npm run test:coverage

# Bot
python job_bot/bot.py
python -m pytest job_bot/tests/ -v
```

### Testing

```bash
# Todos los tests
pytest jobbot/ -v --tb=short

# Tests específicos
pytest api/tests/test_auth.py -v
pytest api/tests/test_security.py -v

# Dashboard tests
cd dashboard && npm test

# Coverage
pytest --cov=jobbot --cov-report=html
```

### Backup

```bash
# Backup manual
python job_bot/backup.py

# Backup con email
python job_bot/backup.py --email admin@jobbot.ar
```

### Docker

```bash
# Construir y ejecutar
docker-compose up -d --build

# Logs
docker-compose logs -f api
docker-compose logs -f dashboard

# Detener
docker-compose down
```

---

## 📚 Documentación

- 📖 **[API Documentation](api/README.md)** - Endpoints, auth, webhooks
- 🎨 **[Dashboard Docs](dashboard/README.md)** - Componentes, state management
- 🤖 **[Bot Documentation](job_bot/README.md)** - Comandos, scraping, backup
- 🚀 **[Deployment Guide](DEPLOYMENT.md)** - Infraestructura, SSL, monitoring
- 📝 **[Changelog](CHANGELOG.md)** - Historial de versiones

## 🚀 Quick Start (Developer)

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm/pnpm
- Git

### 1. Clone & Setup

```bash
git clone https://github.com/tuusuario/jobbot.git
cd jobbot

# Setup all components
make setup  # Or run setup scripts individually
```

### 2. Backend (API)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r api/requirements.txt

# Run with hot reload
make api-dev
# Or: uvicorn api.main:app --reload --port 8000
```

### 3. Dashboard

```bash
cd dashboard
npm install

# Run dev server
make dashboard-dev
# Or: npm run dev
```

### 4. Bot (Optional)

```bash
cd job_bot
pip install -r requirements.txt
python bot.py
```

### 5. Verify Setup

- API Docs: `http://localhost:8000/docs`
- Dashboard: `http://localhost:3000`
- Health Check: `http://localhost:8000/health`

---

## 📚 API Reference

Complete API documentation available at:

- **Interactive Docs**: `http://localhost:8000/docs` (Swagger UI)
- **API README**: [api/README.md](./api/README.md) - Full endpoints, auth, webhooks
- **Technical Spec**: [docs/TECHNICAL_SPEC.md](./docs/TECHNICAL_SPEC.md)

### Quick Example

```bash
# Login
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pass"}'

# Search jobs
curl http://localhost:8000/jobs/search \
  -H "Authorization: Bearer <token>"
```

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](./CONTRIBUTING.md) for details.

### Quick Guide

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Run tests: `make test`
4. Commit your changes: `git commit -m 'Add amazing feature'`
5. Push to the branch: `git push origin feature/amazing-feature`
6. Open a Pull Request

### Development Commands

```bash
make test          # Run all tests
make test-api      # Run API tests only
make test-dashboard # Run dashboard tests only
make lint          # Run linting
make format        # Format code
```

---

## 📝 Changelog

See [CHANGELOG.md](./CHANGELOG.md) for the complete version history.

**Latest (v1.0.0)**:
- Security hardening: audit logging, CSP, JWT improvements
- Dashboard MVP: 8 pages, dark mode, real-time analytics
- 2,810 lines of tests added
- Multi-platform: Telegram bot + Web dashboard

---

## 📄 License

MIT License - see [LICENSE](./LICENSE) for details.

---

## 👥 Team

**JobBot Technologies** 🚀
- **Nacho (PISCU)** - Founder & CTO
- Former VP Engineering @ MercadoLibre (Advisor)
- YC Alum - B2B SaaS Expert (Advisor)

---

<p align="center">
  <strong>JobBot</strong> - Automating your tech career search with AI
  <br>
  🚀 v1.0.0 | Buenos Aires, Argentina | 2024
</p>

# 🚀 JobBot Deployment Guide

Guía completa para desplegar JobBot en producción.

---

## 📋 Tabla de Contenidos

- [Requisitos](#-requisitos)
- [Arquitectura de Producción](#-arquitectura-de-producción)
- [Configuración](#-configuración)
- [Database](#-database)
- [SSL/TLS](#-ssltls)
- [Webhooks](#-webhooks)
- [Monitoreo](#-monitoreo)
- [Docker Deployment](#-docker-deployment)
- [Railway Deployment](#-railway-deployment)
- [Vercel Deployment](#-vercel-deployment)
- [Checklist Pre-Deploy](#-checklist-pre-deploy)
- [Troubleshooting](#-troubleshooting)

---

## 📦 Requisitos

### Hardware Mínimo

| Componente | Especificación |
|------------|----------------|
| CPU | 2 cores |
| RAM | 2 GB |
| Storage | 20 GB SSD |
| Network | 100 Mbps |

### Software Requerido

- Docker 24.0+
- Docker Compose 2.20+
- Git 2.40+
- Nginx (opcional, para reverse proxy)

### Servicios Externos

| Servicio | Uso | URL |
|----------|-----|-----|
| Stripe | Pagos | https://dashboard.stripe.com |
| MercadoPago | Pagos AR | https://www.mercadopago.com.ar |
| Groq | IA | https://console.groq.com |
| Telegram | Bot | https://t.me/BotFather |
| Supabase | PostgreSQL (opcional) | https://supabase.com |

---

## 🏗️ Arquitectura de Producción

```
┌─────────────────────────────────────────────────────────────┐
│                         USERS                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      CLOUDFLARE/NGINX                       │
│                     (SSL + Rate Limit)                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│  Dashboard   │ │   API    │ │     Bot      │
│  (Vercel)    │ │ (Docker) │ │  (Docker)    │
│  Next.js     │ │ FastAPI  │ │  Telegram    │
└──────────────┘ └────┬─────┘ └──────────────┘
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│   Supabase   │ │  SQLite  │ │    Redis     │
│ (PostgreSQL) │ │  (local) │ │  (cache)     │
└──────────────┘ └──────────┘ └──────────────┘
```

---

## ⚙️ Configuración

### 1. Variables de Entorno (Producción)

Crear archivo `.env.production`:

```env
# ═══════════════════════════════════════════════════════════
# APP
# ═══════════════════════════════════════════════════════════
APP_ENV=production
LOG_LEVEL=WARNING
DEBUG=false

# ═══════════════════════════════════════════════════════════
# DOMAIN & URLS
# ═══════════════════════════════════════════════════════════
API_URL=https://api.jobbot.ar
DASHBOARD_URL=https://app.jobbot.ar
LANDING_URL=https://jobbot.ar
CORS_ORIGINS=https://app.jobbot.ar,https://jobbot.ar

# ═══════════════════════════════════════════════════════════
# JWT (¡CRÍTICO! Cambiar en producción)
# ═══════════════════════════════════════════════════════════
# Generar con: openssl rand -hex 32
JWT_SECRET_KEY=your-super-secret-key-min-32-chars-change-this

# ═══════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════
# Opción 1: SQLite (para single-node)
DATABASE_TYPE=sqlite
DATABASE_PATH=/app/data/job_bot.db

# Opción 2: Supabase (para multi-node/scaling)
# DATABASE_TYPE=supabase
# SUPABASE_URL=https://your-project.supabase.co
# SUPABASE_KEY=your-anon-key

# ═══════════════════════════════════════════════════════════
# TELEGRAM BOT
# ═══════════════════════════════════════════════════════════
TELEGRAM_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11

# ═══════════════════════════════════════════════════════════
# AI / GROQ
# ═══════════════════════════════════════════════════════════
GROQ_API_KEY=gsk_your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile

# ═══════════════════════════════════════════════════════════
# STRIPE
# ═══════════════════════════════════════════════════════════
STRIPE_SECRET_KEY=sk_live_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
STRIPE_PRO_PRICE_ID=price_xxx
STRIPE_PREMIUM_PRICE_ID=price_xxx

# ═══════════════════════════════════════════════════════════
# MERCADOPAGO (Argentina)
# ═══════════════════════════════════════════════════════════
MP_ACCESS_TOKEN=APP_USR-your-access-token
MP_WEBHOOK_SECRET=your_webhook_secret
MP_WEBHOOK_IPS=18.229.181.114,18.228.73.238,54.232.98.147
MP_PRO_PRICE_ID=xxx
MP_PREMIUM_PRICE_ID=xxx

# ═══════════════════════════════════════════════════════════
# RATE LIMITING
# ═══════════════════════════════════════════════════════════
LOGIN_RATE_LIMIT=5
LOGIN_RATE_WINDOW_SECONDS=900
API_RATE_LIMIT=100
API_RATE_WINDOW_SECONDS=60

# ═══════════════════════════════════════════════════════════
# BACKUP
# ═══════════════════════════════════════════════════════════
BACKUP_EMAIL=admin@jobbot.ar
BACKUP_RETENTION_DAYS=30
BACKUP_S3_BUCKET=jobbot-backups
BACKUP_S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx

# ═══════════════════════════════════════════════════════════
# MONITORING
# ═══════════════════════════════════════════════════════════
SENTRY_DSN=https://xxx@sentry.io/xxx
HEALTH_CHECK_TOKEN=secret-token-for-health-checks
```

### 2. Generar Secrets

```bash
# JWT Secret (32 bytes hex)
openssl rand -hex 32

# Webhook Secrets
openssl rand -hex 24
```

---

## 🗄️ Database

### Opción 1: SQLite (Simple)

Para deploys single-node:

```yaml
# docker-compose.yml
volumes:
  - ./data:/app/data
```

### Opción 2: Supabase (Escalable)

1. Crear proyecto en [Supabase](https://supabase.com)
2. Copiar URL y anon key
3. Ejecutar migrations:

```sql
-- schema.sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255),
    plan VARCHAR(50) DEFAULT 'free',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    title VARCHAR(255),
    company VARCHAR(255),
    url TEXT,
    source VARCHAR(50),
    match_score INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- más tablas...
```

---

## 🔒 SSL/TLS

### Opción 1: Cloudflare (Recomendado)

1. Agregar dominio a Cloudflare
2. Configurar DNS:
   ```
   A     api.jobbot.ar    →  <server-ip>
   A     app.jobbot.ar    →  <vercel>
   CNAME jobbot.ar        →  <vercel>
   ```
3. Habilitar "Always Use HTTPS"
4. Modo SSL: "Full (strict)"

### Opción 2: Let's Encrypt + Nginx

```nginx
# /etc/nginx/sites-available/jobbot
server {
    listen 443 ssl http2;
    server_name api.jobbot.ar;

    ssl_certificate /etc/letsencrypt/live/jobbot.ar/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/jobbot.ar/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name api.jobbot.ar;
    return 301 https://$server_name$request_uri;
}
```

---

## 🔔 Webhooks

### Stripe

1. Ir a Stripe Dashboard → Developers → Webhooks
2. Agregar endpoint:
   - URL: `https://api.jobbot.ar/webhooks/stripe`
   - Events:
     - `checkout.session.completed`
     - `invoice.payment_failed`
     - `customer.subscription.deleted`
     - `customer.subscription.updated`
3. Copiar `Signing secret` a `STRIPE_WEBHOOK_SECRET`

### MercadoPago

1. Ir a MercadoPago → Tu aplicación → Webhooks
2. Agregar endpoint:
   - URL: `https://api.jobbot.ar/webhooks/mercadopago`
   - Events: `payment`, `subscription`
3. Verificar IP whitelist configurada

---

## 📊 Monitoreo

### Health Checks

```bash
# Check básico
curl https://api.jobbot.ar/health

# Check detallado (con token)
curl https://api.jobbot.ar/health/detailed \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Logs

```bash
# Ver logs en tiempo real
docker-compose logs -f api

# Ver últimos 100 logs
docker-compose logs --tail=100 api
```

### Métricas (Opcional)

```yaml
# docker-compose.yml con Prometheus
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
```

---

## 🐳 Docker Deployment

### Estructura

```
jobbot/
├── docker-compose.yml
├── Dockerfile.api
├── Dockerfile.bot
├── .env.production
└── nginx/
    └── nginx.conf
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    container_name: jobbot-api
    restart: unless-stopped
    ports:
      - "8000:8000"
    env_file:
      - .env.production
    volumes:
      - ./data:/app/data
      - ./cvs:/app/cvs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - jobbot-network

  bot:
    build:
      context: .
      dockerfile: Dockerfile.bot
    container_name: jobbot-bot
    restart: unless-stopped
    env_file:
      - .env.production
    volumes:
      - ./data:/app/data
      - ./cvs:/app/cvs
    depends_on:
      - api
    networks:
      - jobbot-network

  nginx:
    image: nginx:alpine
    container_name: jobbot-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - api
    networks:
      - jobbot-network

networks:
  jobbot-network:
    driver: bridge
```

### Dockerfile - API

```dockerfile
# Dockerfile.api
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY api/ ./api/
COPY job_bot/ ./job_bot/

# Crear directorios
RUN mkdir -p /app/data /app/cvs

# Puerto
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Dockerfile - Bot

```dockerfile
# Dockerfile.bot
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY job_bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY job_bot/ ./job_bot/

RUN mkdir -p /app/data /app/cvs

CMD ["python", "job_bot/bot.py"]
```

### Deploy

```bash
# 1. Clonar repo
git clone https://github.com/tuusuario/jobbot.git
cd jobbot

# 2. Configurar .env
cp .env.example .env.production
# Editar .env.production con valores de producción

# 3. Iniciar servicios
docker-compose up -d

# 4. Verificar salud
docker-compose ps
curl https://api.jobbot.ar/health

# 5. Ver logs
docker-compose logs -f
```

---

## 🚂 Railway Deployment

### 1. Preparación

```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login
railway login
```

### 2. Deploy API

```bash
cd jobbot/api

# Crear proyecto
railway init

# Variables de entorno
railway variables set APP_ENV=production
railway variables set JWT_SECRET_KEY=$(openssl rand -hex 32)
# ... más variables

# Deploy
railway up

# Dominio
railway domain
```

### 3. Configurar Webhooks

Usar el dominio de Railway para webhooks:
```
https://jobbot-api.up.railway.app/webhooks/stripe
```

---

## ▲ Vercel Deployment (Dashboard)

### 1. Preparación

```bash
cd jobbot/dashboard

# Instalar Vercel CLI
npm i -g vercel

# Login
vercel login
```

### 2. Deploy

```bash
# Configurar proyecto
vercel

# Variables de entorno
vercel env add NEXT_PUBLIC_API_URL
# Valor: https://api.jobbot.ar

# Deploy a producción
vercel --prod
```

### 3. Configuración

```javascript
// next.config.js
const nextConfig = {
  output: 'standalone',
  images: {
    domains: ['api.jobbot.ar'],
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'https://api.jobbot.ar/:path*',
      },
    ]
  },
}

module.exports = nextConfig
```

---

## ✅ Checklist Pre-Deploy

### Seguridad

- [ ] JWT_SECRET_KEY cambiado (min 32 chars)
- [ ] DEBUG=false en producción
- [ ] HTTPS habilitado
- [ ] Webhook secrets configurados
- [ ] Rate limits apropiados
- [ ] Headers de seguridad activos
- [ ] CORS origins restringidos

### Configuración

- [ ] Variables de entorno completas
- [ ] Database migrada/inicializada
- [ ] Webhooks configurados en Stripe/MP
- [ ] Telegram bot configurado
- [ ] Groq API key válida

### Testing

- [ ] Tests pasando: `pytest`
- [ ] Tests dashboard: `npm test`
- [ ] Health checks funcionando
- [ ] Webhooks probados
- [ ] Flujo de login probado

### Monitoreo

- [ ] Logs configurados
- [ ] Health checks activos
- [ ] Sentry configurado (opcional)
- [ ] Backup automático configurado

---

## 🔧 Troubleshooting

### Problema: Bot no responde

```bash
# Verificar logs
docker-compose logs bot

# Verificar token
curl https://api.telegram.org/bot<TELEGRAM_TOKEN>/getMe
```

### Problema: Webhooks fallan

```bash
# Verificar firma
docker-compose logs api | grep webhook

# Probar manualmente
curl -X POST https://api.jobbot.ar/webhooks/stripe \
  -H "Stripe-Signature: test" \
  -d '{}'
```

### Problema: Database locked (SQLite)

```bash
# Verificar permisos
ls -la data/

# Backup y recrear
cp data/job_bot.db data/job_bot.db.backup
rm data/job_bot.db
# Reiniciar contenedor
```

### Problema: Rate limiting muy estricto

```bash
# Verificar headers
curl -I https://api.jobbot.ar/health

# Ajustar límites en .env.production
LOGIN_RATE_LIMIT=10
API_RATE_LIMIT=200
```

---

## 📚 Recursos

- [Docker Docs](https://docs.docker.com/)
- [Railway Docs](https://docs.railway.app/)
- [Vercel Docs](https://vercel.com/docs)
- [Let's Encrypt](https://letsencrypt.org/)
- [Cloudflare SSL](https://www.cloudflare.com/ssl/)

---

<p align="center">
  <strong>JobBot Deployment</strong>
  <br>
  Production Ready 🚀
</p>

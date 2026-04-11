# 🚀 PLAN DE MEJORA DEFINITIVO - JobBot AR
## Para sacar el proyecto a la luz (Production-Ready)

**Fecha:** 2026-04-11  
**Status:** Controlled Launch Beta → Production  
**Security Score:** 85/100 → Target: 95/100  

---

## 📊 ANÁLISIS DE ARQUITECTURA ACTUAL

### Superficies Activas (✅ Canónicas)

| Superficie | Tecnología | Estado | Prioridad |
|------------|------------|--------|-----------|
| `api/` | FastAPI + PostgreSQL | ✅ Funcional | P0 |
| `dashboard/` | Next.js 16 App Router | ✅ Funcional | P0 |
| `job_bot/` | Python Telegram Bot | ✅ Funcional | P0 |

### APIs Existentes

```
/api/v1/
├── auth/          ✅ JWT, cookies httpOnly, registro/login
├── users/         ✅ CRUD usuarios, perfiles
├── jobs/          ✅ Búsqueda, scraping, filtros
├── subscriptions/ ✅ Stripe + MercadoPago, planes Free/Starter/Pro/Premium
├── credits/       ✅ CV Suite unlock, 4 packs de créditos
├── cv/            ✅ ATS scoring, match, cover letters, mock interviews
├── admin/         ✅ Panel admin, métricas
└── public/        ✅ Health checks, webhooks
```

### Features Productivas (✅ Launch Ready)

| Feature | Estado | Verificación |
|---------|--------|--------------|
| Auth real con JWT | ✅ | Cookies httpOnly, refresh tokens |
| Dashboard real | ✅ | 0% mock data, PostgreSQL |
| Pipeline postulaciones | ✅ | CRUD completo, kanban view |
| Checkout funcional | ✅ | Stripe + MP + webhooks |
| Planes de precios | ✅ | Free/Starter($4)/Pro($8)/Premium($12) |
| CV Suite | ✅ | ATS + match + cover letters (Groq) |
| Bot Telegram | ✅ | 14 comandos, alertas programadas |
| Landing Next.js | ✅ | SSR, SEO, CTAs reales |
| Cache Redis | ✅ | Endpoints críticos |
| Workers Celery | ✅ | Async scraping, notificaciones |
| Health endpoints | ✅ | `/health/ready` para ALB |

---

## 🎯 PLAN DE MEJORA - 4 FASES

### 🔴 FASE 1: SEGURIDAD & HARDENING (P0 - CRÍTICO)

**Objetivo:** Subir security score de 85/100 a 95/100

#### 1.1 Secrets Management
- [ ] Rotar todos los secrets (JWT_SECRET, API keys)
- [ ] Mover secrets a Railway/Vercel environment (no .env files)
- [ ] Validar que ningún secret esté hardcodeado:
  ```bash
  grep -r "sk_live\|sk_test\|password\|secret" --include="*.py" api/ job_bot/
  ```

#### 1.2 Input Validation & Sanitization
- [ ] Agregar Zod schemas en TODOS los endpoints de API
- [ ] Sanitizar inputs del bot Telegram (HTML escaping)
- [ ] Validar file uploads (CVs) - tamaño, tipo, malware scan

#### 1.3 Rate Limiting Refinement
- [ ] Endpoints de auth: 5 intentos/minuto (ya implementado ✅)
- [ ] API general: 100 req/min por IP (ya implementado ✅)
- [ ] Búsquedas: 20 req/min por usuario
- [ ] Webhooks: 50 req/min por provider

#### 1.4 CORS & Security Headers
- [ ] Reducir CORS origins a dominios productivos exactos
- [ ] Agregar CSP headers estrictos
- [ ] Habilitar HSTS (HTTP Strict Transport Security)

#### 1.5 Database Security
- [ ] Row Level Security (RLS) en PostgreSQL para usuarios
- [ ] Encriptar PII sensible (emails, teléfonos)
- [ ] Audit logging en operaciones críticas (ya implementado ✅)

**Tiempo estimado:** 2-3 días  
**Verificación:** `npm audit`, `pip-audit`, penetration testing básico

---

### 🟠 FASE 2: CI/CD & DEPLOYMENT (P0 - CRÍTICO)

**Objetivo:** Pipeline automatizado, zero-downtime deploys

#### 2.1 GitHub Actions CI/CD

```yaml
# .github/workflows/deploy.yml
name: CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r api/requirements.txt
      - run: pytest api/tests/ -v --cov=api --cov-report=xml
      
  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
      - run: cd dashboard && npm ci
      - run: cd dashboard && npm run lint
      - run: cd dashboard && npm run typecheck
      - run: cd dashboard && npm run build
      
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install bandit safety
      - run: bandit -r api/ -f json -o bandit-report.json || true
      - run: safety check -r api/requirements.txt || true
      
  deploy-staging:
    needs: [test-backend, test-frontend, security-scan]
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Railway Staging
        run: railway up --service api-staging
        
  deploy-production:
    needs: [test-backend, test-frontend, security-scan]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      - name: Deploy API to Railway
        run: railway up --service api-production
      - name: Deploy Dashboard to Vercel
        run: vercel --prod --yes
      - name: Health Check
        run: curl -f https://api.jobbot.ar/health/ready
```

#### 2.2 Railway Configuration

```json
// railway.json (API)
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4",
    "healthcheckPath": "/health/ready",
    "healthcheckTimeout": 30,
    "restartPolicyType": "ON_FAILURE",
    "numReplicas": 2
  }
}
```

#### 2.3 Vercel Configuration (Dashboard)

```json
// dashboard/vercel.json
{
  "installCommand": "npm install --legacy-peer-deps",
  "buildCommand": "npm run build",
  "framework": "nextjs",
  "regions": ["scl1"],
  "functions": {
    "src/app/api/**/*.ts": {
      "maxDuration": 30
    }
  }
}
```

#### 2.4 Docker Optimization

```dockerfile
# Multi-stage build para API
FROM python:3.11-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/
COPY api/requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim AS runner
WORKDIR /app
RUN apt-get update && apt-get install -y libpq5 && rm -rf /var/lib/apt/lists/
COPY --from=builder /root/.local /root/.local
COPY api/ ./api/
COPY job_bot/ ./job_bot/
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost:8000/health/ready || exit 1
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

#### 2.5 Health Checks & Monitoring

```python
# api/routes/health.py - Ya implementado ✅
# Verificar que estén activos:
GET /health/ready     # Readiness probe
GET /health/live      # Liveness probe
GET /health/detailed  # DB, Redis, external APIs status
```

**Tiempo estimado:** 2-3 días  
**Verificación:** Deploy a staging → smoke tests → deploy a producción

---

### 🟡 FASE 3: PERFORMANCE & ESCALABILIDAD (P1 - IMPORTANTE)

**Objetivo:** Soportar 1000+ usuarios concurrentes

#### 3.1 Database Optimization
- [ ] Connection pooling (PgBouncer)
- [ ] Índices en queries frecuentes:
  ```sql
  CREATE INDEX CONCURRENTLY idx_jobs_search ON jobs(title, company, location);
  CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
  CREATE INDEX CONCURRENTLY idx_applications_user ON applications(user_id, status);
  ```
- [ ] Query optimization (eliminar N+1 queries)
- [ ] Read replicas para queries de reportes

#### 3.2 Caching Strategy

```python
# Implementar en endpoints críticos
@cache.cached(timeout=300, key_prefix='jobs_search')
async def search_jobs(query: str, filters: dict):
    # ... lógica de búsqueda
    
@cache.cached(timeout=60, key_prefix='user_profile')
async def get_user_profile(user_id: str):
    # ... fetch user
```

#### 3.3 CDN & Static Assets
- [ ] Cloudflare / AWS CloudFront para dashboard
- [ ] Optimizar imágenes (WebP, lazy loading)
- [ ] Bundle size optimization (Next.js code splitting)

#### 3.4 Async Workers
- [ ] Celery + Redis ya implementados ✅
- [ ] Monitorear queue depth y worker health
- [ ] Auto-scaling de workers por carga

**Tiempo estimado:** 3-4 días  
**Verificación:** Load testing con k6/Artillery

---

### 🟢 FASE 4: UX & FEATURES FINALES (P2 - NICE TO HAVE)

**Objetivo:** Polish final, analytics, GDPR

#### 4.1 Analytics & Tracking
- [ ] PostHog / Mixpanel para funnel conversion
- [ ] Track: signup → trial → subscription → churn
- [ ] Dashboard de métricas para admin

#### 4.2 GDPR Compliance
- [ ] Endpoint `/user/export-data` (JSON dump completo)
- [ ] Endpoint `/user/delete-account` (soft delete + anonimización)
- [ ] Privacy policy actualizada
- [ ] Cookie consent banner

#### 4.3 UX Polish
- [ ] Email templates transaccionales (SendGrid/Resend)
- [ ] Onboarding wizard para nuevos usuarios
- [ ] Empty states ilustrados
- [ ] Loading skeletons

#### 4.4 Features Post-Launch
- [ ] Referral program ("Invita un amigo, 1 mes gratis")
- [ ] Job alerts por email (además de Telegram)
- [ ] Mobile app (React Native / Flutter)
- [ ] Chrome extension para job matching

**Tiempo estimado:** 5-7 días (post-launch)  
**Verificación:** User testing, NPS surveys

---

## 🚀 CHECKLIST PRE-LAUNCH (P0 - OBLIGATORIO)

### Seguridad
- [ ] Security audit con `bandit`, `safety`, `npm audit`
- [ ] Penetration testing básico (OWASP Top 10)
- [ ] Secrets rotados y en environment variables
- [ ] HTTPS forzado en todas las superficies
- [ ] Rate limiting activo en todos los endpoints

### Performance
- [ ] Load testing: 1000 usuarios concurrentes
- [ ] Database con índices optimizados
- [ ] Cache funcionando en endpoints críticos
- [ ] Bundle size < 500KB (dashboard)

### Deployment
- [ ] CI/CD pipeline funcionando
- [ ] Staging environment deployado
- [ ] Rollback plan documentado
- [ ] Health checks activos
- [ ] Logs centralizados (Railway/Vercel)

### Legal/Compliance
- [ ] Términos y condiciones
- [ ] Política de privacidad (GDPR compliant)
- [ ] Cookie consent
- [ ] Derecho al olvido implementado

### Monitoreo
- [ ] Alertas por email/SMS si API cae
- [ ] Dashboard de métricas básico
- [ ] Error tracking (Sentry)

---

## 📅 CRONOGRAMA PROPUESTO

| Fase | Duración | Fecha Inicio | Fecha Fin |
|------|----------|--------------|-----------|
| Fase 1: Seguridad | 3 días | Día 1 | Día 3 |
| Fase 2: CI/CD | 3 días | Día 4 | Día 6 |
| Fase 3: Performance | 4 días | Día 7 | Día 10 |
| Testing & QA | 2 días | Día 11 | Día 12 |
| **LAUNCH** | - | **Día 13** | - |
| Fase 4: Post-launch | 7 días | Día 14+ | Continuo |

**Total para Launch:** ~2 semanas  
**Total con Post-launch:** ~1 mes

---

## 🎯 PROXIMOS PASOS INMEDIATOS

1. **Hoy:** Aplicar Fase 1 (Seguridad)
2. **Mañana:** Configurar CI/CD (Fase 2)
3. **Esta semana:** Load testing y optimización (Fase 3)
4. **Próxima semana:** LAUNCH 🚀

---

## 📈 MÉTRICAS DE ÉXITO

| Métrica | Target | Cómo medir |
|---------|--------|------------|
| Security Score | >95/100 | `bandit` + `npm audit` |
| Uptime | 99.9% | Railway/Vercel dashboards |
| API Latencia p95 | <200ms | Logs de request time |
| Error Rate | <0.1% | Sentry / logs |
| Conversion Free→Paid | >5% | PostHog funnel |
| NPS Score | >50 | Survey a usuarios |

---

**Documento generado con:** Skills de deployment-patterns, backend-patterns, frontend-patterns, security-review, verification-before-completion  
**Estado:** Listo para implementación  
**Próximo paso:** Priorizar Fase 1 (Seguridad) y comenzar ejecución

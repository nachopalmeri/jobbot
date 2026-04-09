# Plan de Mejora JobBot - Silicon Valley Standards

> **Fecha:** Abril 2026  
> **Periodo:** 4 Semanas (MVP Production-Ready)  
> **Agente:** ARCHITECT - Antigravity  
> **Metodología:** SV Sprint Planning

---

## 🎯 Objetivo del Plan

Transformar JobBot de MVP+ (73/100) a Production-Ready SV Grade (85+/100) en 4 semanas para:
1. **Product Hunt Launch** (Week 4)
2. **YC Application Ready** (Week 4)
3. **Primeros 100 paying customers** (Week 8)

---

## 📊 Baseline vs Target

| Métrica | Baseline | Week 4 Target | Week 8 Target |
|---------|----------|---------------|---------------|
| Overall Score | 73/100 | 85+/100 | 90+/100 |
| Landing LCP | ~3.5s | <2s | <1.5s |
| API p95 | 150ms | <100ms | <80ms |
| Dashboard Integration | Mock | Real | Real-time |
| MRR | $0 | $1K | $5K |
| Users | 1,000 | 3,000 | 8,000 |
| Test Coverage | 70% | 80% | 85% |

---

## 🗓️ Semana 1: Foundation (P0 - Bloqueadores Críticos)

**Meta:** Resolver issues que bloquean launch completamente

### Día 1-3: Landing Page Migration

#### Task 1.1: Next.js Scaffold
**Owner:** Frontend Dev  
**Effort:** 8h  
**Priority:** P0 🔴

```bash
# Crear proyecto Next.js 16
npx create-next-app@latest jobbot-landing \
  --typescript \
  --tailwind \
  --eslint \
  --app \
  --src-dir \
  --import-alias "@/*"
```

- [ ] Setup Next.js 16 con App Router
- [ ] Configurar Tailwind v4
- [ ] Migrar design tokens CSS → Tailwind config
- [ ] Setup shadcn/ui
- [ ] Configurar next/image para optimización

**Done When:**
- [ ] `npm run build` exitoso
- [ ] Lighthouse score >70 en localhost

---

#### Task 1.2: Componentización Landing
**Owner:** Frontend Dev  
**Effort:** 16h  
**Priority:** P0 🔴

**Estrategia:** Extraer componentes del HTML monolítico

```typescript
// Componentes a crear:
app/
├── sections/
│   ├── Hero.tsx           # Hero + CTA principal
│   ├── Features.tsx       # Feature grid
│   ├── HowItWorks.tsx     # Steps
│   ├── Pricing.tsx        # Pricing table
│   ├── Testimonials.tsx   # Social proof
│   └── FAQ.tsx            # Accordion FAQ
├── components/
│   ├── Navbar.tsx
│   ├── Footer.tsx
│   ├── CTA.tsx            # Reusable CTA buttons
│   └── DarkModeToggle.tsx
```

**Migration Map (7,647 líneas → componentes):**

| Sección | Líneas HTML | Componente | Status |
|---------|-------------|------------|--------|
| CSS Variables | 200 | tailwind.config.ts | ⬜ |
| Navbar | ~400 | Navbar.tsx | ⬜ |
| Hero | ~800 | Hero.tsx | ⬜ |
| Features | ~1200 | Features.tsx | ⬜ |
| How It Works | ~600 | HowItWorks.tsx | ⬜ |
| Pricing | ~700 | Pricing.tsx | ⬜ |
| Testimonials | ~400 | Testimonials.tsx | ⬜ |
| FAQ | ~500 | FAQ.tsx | ⬜ |
| Footer | ~300 | Footer.tsx | ⬜ |
| Animations | ~800 | hooks/useAnimations.ts | ⬜ |
| **Total** | **~7,647** | **12 componentes** | |

- [ ] Extraer Hero section (líneas 200-1000 del HTML)
- [ ] Extraer Features section
- [ ] Extraer Pricing section
- [ ] Migrar animaciones GSAP → Framer Motion
- [ ] Implementar dark mode con next-themes

**Done When:**
- [ ] Todos los componentes renderizan correctamente
- [ ] Responsive funciona (mobile → desktop)
- [ ] Dark mode toggle funciona

---

#### Task 1.3: Performance Optimization
**Owner:** Frontend Dev  
**Effort:** 8h  
**Priority:** P0 🔴

- [ ] Optimizar todas las imágenes con next/image
- [ ] Lazy loading para secciones debajo del fold
- [ ] Preload fonts críticos (Sora, DM Sans)
- [ ] Bundle analysis: `npm run analyze`
- [ ] Target: <50KB bundle inicial

**Done When:**
- [ ] Lighthouse Performance >80
- [ ] LCP <2.5s en 4G throttling

---

### Día 3-5: API Integration

#### Task 1.4: Dashboard Data Fetching
**Owner:** Fullstack Dev  
**Effort:** 12h  
**Priority:** P0 🔴

**Problema actual:** Todos los datos son mock

```typescript
// Antes (mock):
const statsData = [{ title: 'Jobs Aplicados', value: '12', ... }]

// Después (real):
const { data: stats, isLoading } = useQuery({
  queryKey: ['stats'],
  queryFn: () => api.get('/api/v1/dashboard/stats'),
  staleTime: 5 * 60 * 1000, // 5 min cache
});
```

- [ ] Instalar React Query (TanStack Query)
- [ ] Crear API client con Axios + interceptors
- [ ] Migrar Dashboard page → data real
- [ ] Migrar Buscar page → data real
- [ ] Migrar Postulaciones page → data real
- [ ] Migrar Perfil page → data real
- [ ] Loading states con skeletons
- [ ] Error states con retry

**API Endpoints Needed:**
```
GET /api/v1/dashboard/stats
GET /api/v1/jobs/search?query=&location=
GET /api/v1/applications
GET /api/v1/users/me
GET /api/v1/users/me/profile
PUT /api/v1/users/me/profile
```

**Done When:**
- [ ] Dashboard muestra datos reales del usuario logueado
- [ ] No hay más "12" hardcodeado en stats
- [ ] Jobs list viene de la API

---

#### Task 1.5: Auth Real (NextAuth.js)
**Owner:** Backend Dev  
**Effort:** 8h  
**Priority:** P0 🔴

**Problema actual:** LocalStorage auth (inseguro, no SSR)

```typescript
// Antes (problemático):
useEffect(() => {
  const token = localStorage.getItem('token');
  if (!token) window.location.href = '/login';
}, []);

// Después (SSR-safe):
// middleware.ts
export { default } from "next-auth/middleware"
export const config = { matcher: ["/dashboard/:path*"] }
```

- [ ] Instalar NextAuth.js v5
- [ ] Configurar credentials provider (email/password)
- [ ] Setup JWT strategy
- [ ] Crear middleware.ts para protección de rutas
- [ ] Migrar dashboard layout → SSR auth
- [ ] Logout funcional

**Done When:**
- [ ] /dashboard redirige a /login si no hay sesión
- [ ] Login crea sesión JWT válida
- [ ] No hay localStorage.getItem('token')

---

### Día 5-7: Database Migration

#### Task 1.6: PostgreSQL Migration
**Owner:** Backend/DevOps  
**Effort:** 8h  
**Priority:** P0 🔴

**Problema:** SQLite en producción (no scalable)

```bash
# Setup PostgreSQL
# Opción A: Supabase (recomendado para YC)
supabase link --project-ref xxx

# Opción B: AWS RDS
# Opción C: Railway/Render
```

- [ ] Setup PostgreSQL instance
- [ ] Instalar psycopg2-binary + sqlalchemy[postgresql]
- [ ] Migrar models.py → PostgreSQL dialect
- [ ] Connection pooling (PgBouncer)
- [ ] Database migrations (Alembic)
- [ ] Data migration script (SQLite → PostgreSQL)

**Code Changes:**
```python
# database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

DATABASE_URL = "postgresql+asyncpg://user:pass@host/db"
engine = create_async_engine(DATABASE_URL, pool_size=20, max_overflow=30)
```

**Done When:**
- [ ] API conecta a PostgreSQL
- [ ] Tests pasan con PostgreSQL
- [ ] 100 concurrent requests no crashean

---

### Week 1 Milestones

| Milestone | Status | Verificación |
|-----------|--------|--------------|
| Landing Next.js | ⬜ | Lighthouse >70 |
| Dashboard API integration | ⬜ | Datos reales visibles |
| PostgreSQL migration | ⬜ | Load test 100 RPS OK |
| NextAuth.js | ⬜ | SSR auth funciona |

---

## 🗓️ Semana 2: Scale & Convert (P1 - Growth Blockers)

**Meta:** Habilitar revenue y performance a escala

### Día 8-10: Stripe Integration

#### Task 2.1: Stripe Checkout Flow
**Owner:** Fullstack Dev  
**Effort:** 12h  
**Priority:** P1 🟠

**Flujo objetivo:**
```
Usuario → Clic "Upgrade" → Stripe Checkout → Webhook → Pro tier activo
```

- [ ] Setup Stripe account
- [ ] Crear products: Free, Pro ($12/mes), Enterprise
- [ ] Implementar Stripe Checkout Session
- [ ] Webhook handler (`/api/webhooks/stripe`)
- [ ] Subscription status sync
- [ ] Billing portal (customer.self-service)
- [ ] Invoice emails

**API Endpoints:**
```python
# subscriptions.py
@router.post("/checkout-session")
async def create_checkout_session(plan: str, user: User = Depends(get_current_user)):
    session = stripe.checkout.Session.create(
        customer=user.stripe_customer_id,
        line_items=[{"price": plan_price_id, "quantity": 1}],
        mode="subscription",
        success_url=settings.FRONTEND_URL + "/dashboard/suscripcion?success=true",
        cancel_url=settings.FRONTEND_URL + "/dashboard/suscripcion?canceled=true",
    )
    return {"sessionId": session.id}

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    # Handle checkout.completed, invoice.paid, etc.
```

**Frontend:**
```typescript
// suscripcion/page.tsx
const handleUpgrade = async (plan: 'pro' | 'enterprise') => {
  const { sessionId } = await api.post('/api/v1/checkout-session', { plan });
  const stripe = await loadStripe(process.env.NEXT_PUBLIC_STRIPE_KEY);
  await stripe.redirectToCheckout({ sessionId });
};
```

- [ ] Página /suscripcion con pricing cards
- [ ] Botón "Upgrade" en dashboard
- [ ] Feature gating basado en subscription tier
- [ ] "Pro" badge en UI

**Done When:**
- [ ] Primer pago de prueba exitoso
- [ ] Webhook actualiza DB correctamente
- [ ] Usuario puede cancelar subscription

---

#### Task 2.2: Feature Gating
**Owner:** Frontend Dev  
**Effort:** 8h  
**Priority:** P1 🟠

**Lógica:**
```typescript
// hooks/useSubscription.ts
export function useFeatureGating(feature: Feature) {
  const { subscription } = useSubscription();
  
  const limits = {
    free: { maxJobs: 5, hasAI: false, hasWarmIntros: false },
    pro: { maxJobs: Infinity, hasAI: true, hasWarmIntros: true },
    enterprise: { maxJobs: Infinity, hasAI: true, hasWarmIntros: true, hasAPI: true },
  };
  
  return {
    canAccess: limits[subscription.tier][feature],
    showPaywall: !limits[subscription.tier][feature],
  };
}
```

- [ ] Implementar useSubscription hook
- [ ] Crear componente `<Paywall feature="ai-matching" />`
- [ ] Upgrade triggers contextuales
- [ ] Free tier limits: 5 jobs, no AI, no warm intros

**Done When:**
- [ ] Usuario Free ve paywall al intentar añadir job #6
- [ ] Usuario Free ve teaser de AI matching
- [ ] Upgrade modal funciona

---

### Día 10-12: Performance & Caching

#### Task 2.3: Redis Caching
**Owner:** Backend Dev  
**Effort:** 8h  
**Priority:** P1 🟠

**Target:** API p95 <100ms (actual: 150ms)

```python
# core/cache.py (ya existe, activar)
from redis import Redis
from functools import wraps

redis_client = Redis(host='localhost', port=6379, db=0, decode_responses=True)

def cache_response(ttl=300):  # 5 min default
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args))}"
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator

# Uso:
@router.get("/jobs/search")
@cache_response(ttl=300)
async def search_jobs(query: str, location: str):
    # ... expensive query
```

**Endpoints a cachear:**
- [ ] `GET /jobs/search` - TTL 1h (jobs no cambian tan rápido)
- [ ] `GET /dashboard/stats` - TTL 5min
- [ ] `GET /users/me` - TTL 15min
- [ ] `GET /applications` - TTL 5min

- [ ] Setup Redis (Upstash/Railway/Redis Cloud)
- [ ] Implementar cache decorator
- [ ] Cache invalidation strategy
- [ ] Cache hit rate monitoring

**Done When:**
- [ ] API p95 <100ms con cache
- [ ] Cache hit rate >70%

---

#### Task 2.4: Async Workers (Celery)
**Owner:** Backend Dev  
**Effort:** 10h  
**Priority:** P1 🟠

**Problema:** Web scraping bloquea requests

```python
# tasks/scraping.py
from celery import Celery

app = Celery('jobbot', broker='redis://localhost:6379/1')

@app.task
def scrape_jobs_portal(portal: str, query: str):
    # Heavy scraping work
    jobs = scraper.scrape(portal, query)
    store_jobs_in_db(jobs)
    notify_users_of_matches(jobs)

@app.task
def optimize_cv_task(cv_id: str, job_description: str):
    # AI processing (slow)
    optimized = ai_service.optimize(cv_id, job_description)
    save_optimized_cv(cv_id, optimized)
```

- [ ] Setup Celery + Redis broker
- [ ] Mover scraping a background tasks
- [ ] Mover AI processing a background tasks
- [ ] Flower dashboard (Celery monitoring)
- [ ] Retry logic para failed tasks

**Done When:**
- [ ] Request de scraping retorna inmediatamente (job queued)
- [ ] Flower muestra tasks procesándose
- [ ] Failed tasks se reintentan automáticamente

---

### Día 12-14: Analytics & Tracking

#### Task 2.5: Product Analytics Stack
**Owner:** Growth/Dev  
**Effort:** 8h  
**Priority:** P1 🟠

**Stack:**
- **Amplitude:** Product analytics (funnels, retention)
- **PostHog:** Open source alternative (self-host)
- **Google Analytics 4:** Web traffic
- **Mixpanel:** Opcional (redundante con Amplitude)

**Recomendación:** PostHog (open source, eventos ilimitados, autocapture)

```typescript
// lib/analytics.ts
import posthog from 'posthog-js';

export function initAnalytics() {
  posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY, {
    api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST,
    autocapture: true,
    capture_pageview: true,
  });
}

export function track(event: string, properties?: Record<string, any>) {
  posthog.capture(event, properties);
}

// Uso:
track('job_applied', { job_id, company, method: 'manual' });
track('subscription_upgraded', { from: 'free', to: 'pro', revenue: 12 });
track('feature_used', { feature: 'cv_optimizer', tier: 'pro' });
```

**Eventos a trackear:**
- [ ] Signup funnel (signup → profile_complete → first_job_search → first_application)
- [ ] Feature usage (job_search, cv_optimizer, applications, alerts)
- [ ] Subscription events (viewed_pricing, started_checkout, subscribed, canceled)
- [ ] Engagement (DAU, WAU, session duration)

**Dashboards:**
- [ ] Signup conversion funnel
- [ ] Feature adoption
- [ ] Revenue dashboard
- [ ] Retention cohorts

**Done When:**
- [ ] Eventos llegan a PostHog
- [ ] Funnel de signup visible
- [ ] Revenue tracking funciona

---

### Week 2 Milestones

| Milestone | Status | Verificación |
|-----------|--------|--------------|
| Stripe integration | ⬜ | Primer pago real |
| Feature gating | ⬜ | Paywalls funcionan |
| Redis caching | ⬜ | p95 <100ms |
| Celery workers | ⬜ | Scraping async |
| Analytics stack | ⬜ | Eventos trackeados |

---

## 🗓️ Semana 3: Polish & QA (P1 Continuación + P2)

**Meta:** Calidad SV-grade, accesibilidad, testing

### Día 15-17: Accessibility & UX

#### Task 3.1: A11y Audit & Fixes
**Owner:** Frontend Dev  
**Effort:** 8h  
**Priority:** P1 🟠

**Herramientas:**
- axe DevTools (Chrome extension)
- Lighthouse Accessibility audit
- WAVE (Web Accessibility Evaluator)

**Issues típicos a fixear:**
- [ ] Missing alt text en imágenes
- [ ] Insufficient color contrast (WCAG 4.5:1)
- [ ] Missing ARIA labels
- [ ] Keyboard navigation gaps
- [ ] Focus indicators inconsistentes
- [ ] Form labels no asociados

**Fixes:**
```tsx
// Antes (mal):
<img src="/hero.jpg" />
<button onClick={handleClick}>

// Después (bien):
<img src="/hero.jpg" alt="JobBot dashboard mostrando matches de empleo" />
<button onClick={handleClick} aria-label="Buscar empleos" tabIndex={0}>
```

- [ ] Audit completo con axe
- [ ] Fix todos los issues Critical y Serious
- [ ] Keyboard navigation test
- [ ] Screen reader test (NVDA/VoiceOver)

**Done When:**
- [ ] Lighthouse Accessibility >90
- [ ] 0 issues Critical en axe

---

#### Task 3.2: Mobile Optimization
**Owner:** Frontend Dev  
**Effort:** 6h  
**Priority:** P2 🟡

- [ ] Test en dispositivos reales (iOS Safari, Android Chrome)
- [ ] Touch targets >= 44x44px
- [ ] Viewport meta tags correctos
- [ ] No horizontal scroll
- [ ] Font size readable (16px+ sin zoom)
- [ ] Responsive images (srcset)

**Done When:**
- [ ] Dashboard usable en iPhone SE
- [ ] 0 scroll horizontal

---

### Día 17-19: Testing & QA

#### Task 3.3: Frontend Testing
**Owner:** QA/Frontend  
**Effort:** 10h  
**Priority:** P2 🟡

**Stack:**
- Vitest (ya configurado)
- React Testing Library
- MSW (Mock Service Worker) para API mocks
- Playwright (E2E)

```typescript
// __tests__/dashboard.test.tsx
import { render, screen } from '@testing-library/react';
import DashboardPage from '@/app/(dashboard)/page';
import { server } from '@/mocks/server';

describe('Dashboard', () => {
  it('renders stats from API', async () => {
    server.use(
      rest.get('/api/v1/dashboard/stats', (req, res, ctx) => {
        return res(ctx.json({ jobs_applied: 12, interviews: 4 }));
      })
    );
    
    render(<DashboardPage />);
    expect(await screen.findByText('12')).toBeInTheDocument();
    expect(await screen.findByText('Jobs Aplicados')).toBeInTheDocument();
  });
});
```

- [ ] Setup MSW (mock API responses)
- [ ] Tests para Dashboard page
- [ ] Tests para componentes críticos (Card, Button, forms)
- [ ] Tests para auth flows
- [ ] E2E tests con Playwright (critical paths)

**Critical Paths a testear:**
- [ ] Signup → Login → Dashboard
- [ ] Job search → Save job → Apply
- [ ] Upgrade Free → Pro (Stripe)
- [ ] Profile update

**Done When:**
- [ ] Frontend coverage >60%
- [ ] E2E tests pasan en CI

---

#### Task 3.4: Security Audit Final
**Owner:** Security/Dev  
**Effort:** 6h  
**Priority:** P2 🟡

- [ ] Run OWASP ZAP scan
- [ ] Dependency audit: `npm audit`, `pip audit`
- [ ] Secrets scan (gitLeaks/truffleHog)
- [ ] CORS configuration review
- [ ] Rate limiting test (intento de DoS)
- [ ] Input validation fuzzing

**Done When:**
- [ ] 0 vulnerabilidades Critical/High
- [ ] Security score >85/100

---

### Día 19-21: Content & Assets

#### Task 3.5: Demo Video/GIF
**Owner:** Content/Design  
**Effort:** 8h  
**Priority:** P1 🟠

**Especificaciones Product Hunt:**
- Thumbnail: 1024x1024 (logo + tagline)
- Gallery: 5-8 screenshots (GIFs preferidos)
- Video: 30-60 segundos (opcional pero recomendado)

- [ ] Grabar demo de dashboard (Screen Studio/Loom)
- [ ] Editar a 30-60 segundos
- [ ] Añadir captions
- [ ] Exportar GIFs para gallery
- [ ] Crear thumbnail 1024x1024
- [ ] Screenshots de features clave

**Done When:**
- [ ] Video demo subido a YouTube/Vimeo
- [ ] 5-8 gallery assets listos
- [ ] Thumbnail 1024x1024 exportado

---

### Week 3 Milestones

| Milestone | Status | Verificación |
|-----------|--------|--------------|
| Accessibility >90 | ⬜ | Lighthouse |
| Mobile optimized | ⬜ | iPhone test |
| Frontend tests | ⬜ | Coverage >60% |
| Security audit | ⬜ | 0 Critical issues |
| Demo video | ⬜ | 60 segundos |

---

## 🗓️ Semana 4: Launch Prep (GTM)

**Meta:** Todo listo para Product Hunt launch

### Día 22-24: GTM Infrastructure

#### Task 4.1: Email Capture & CRM
**Owner:** Growth  
**Effort:** 6h  
**Priority:** P0 🔴

- [ ] Setup email capture en landing (ConvertKit/Mailchimp)
- [ ] Lead magnets (salary report, CV template)
- [ ] Welcome email sequence (5 emails)
- [ ] Early access list: 500+ emails

**Welcome Sequence:**
1. **Email 1 (inmediato):** Bienvenido + quick win guide
2. **Email 2 (día 1):** Cómo usar JobBot (tutorial)
3. **Email 3 (día 3):** Case study + social proof
4. **Email 4 (día 7):** Offer Pro trial
5. **Email 5 (día 14):** Feedback request + refer a friend

**Done When:**
- [ ] 500+ emails en lista
- [ ] Welcome sequence automática

---

#### Task 4.2: Product Hunt Assets
**Owner:** Growth  
**Effort:** 8h  
**Priority:** P0 🔴

**Product Hunt Page:**
```
Name: JobBot
Tagline: Automate your job search. Get hired faster. (59 chars)
Description: JobBot is an AI-powered job search assistant for developers in LATAM. 
We automate job discovery, optimize your CV for each application, and track your 
progress - saving you 20+ hours per week. (260 chars)
Topics: Productivity, Developer Tools, Career, AI
```

- [ ] Tagline optimizada (≤60 chars)
- [ ] Descripción (≤260 chars)
- [ ] Maker comment #1 (storytelling)
- [ ] Maker comment #2 (use cases)
- [ ] Gallery ordenada (hero, features, pricing, testimonial, dashboard)
- [ ] Video link

**Done When:**
- [ ] Product Hunt draft page completa

---

#### Task 4.3: Discord Community
**Owner:** Community  
**Effort:** 4h  
**Priority:** P1 🟠

- [ ] Crear Discord server
- [ ] Setup canales: #general, #help, #jobs, #feedback, #showcase
- [ ] Roles: Early Adopter, Pro, Admin, Moderator
- [ ] Welcome bot (Carl-bot/Mee6)
- [ ] Integración con JobBot (comandos /jobs, /stats)

**Done When:**
- [ ] Discord server público
- [ ] 50+ miembros iniciales

---

### Día 24-26: Launch Week Prep

#### Task 4.4: Content Calendar
**Owner:** Content  
**Effort:** 6h  
**Priority:** P1 🟠

**Launch Week (D-3 a D+7):**

| Día | Plataforma | Contenido |
|-----|------------|-----------|
| D-3 | LinkedIn | "Estamos lanzando en Product Hunt esta semana"
| D-2 | Twitter | Behind the scenes thread
| D-1 | Email | "Tomorrow we launch" + early access reminder
| D-0 | Product Hunt | Launch!
| D-0 | LinkedIn | Personal story post
| D-0 | Twitter | "We're live!" thread
| D-0 | Telegram | Announce en comunidades BA Tech, etc.
| D+1 | Indie Hackers | "How we built JobBot" post
| D+3 | Hacker News | Show HN
| D+7 | Blog | Launch retrospective + metrics

- [ ] Escribir todos los posts
- [ ] Preparar imágenes/gráficos
- [ ] Schedule en Buffer/Later
- [ ] Coordenar con influencer friends

**Done When:**
- [ ] 10+ posts escritos
- [ ] Calendar scheduleado

---

#### Task 4.5: Support Readiness
**Owner:** Support  
**Effort:** 4h  
**Priority:** P2 🟡

- [ ] Help Center (Crisp/Intercom/Notion)
- [ ] FAQ completo (20+ preguntas)
- [ ] Video tutorials (3x 2min)
- [ ] Chat support (Crisp/Intercom widget)
- [ ] Discord support channel staffed

**Done When:**
- [ ] Help Center público
- [ ] Response time objetivo: <2h

---

### Día 26-28: Final QA

#### Task 4.6: End-to-End Testing
**Owner:** QA/All  
**Effort:** 6h  
**Priority:** P0 🔴

**User Journeys a testear:**
1. **Signup Flow:** Landing → Email capture → Signup → Onboarding → Dashboard
2. **Job Search:** Dashboard → Buscar → Filtros → Guardar job → Aplicar
3. **Upgrade:** Dashboard → Suscripción → Stripe → Pro activated → Feature unlocked
4. **Profile:** Perfil → Editar → Guardar → Cambios persisten

- [ ] Test en producción (staging env)
- [ ] Test en múltiples devices
- [ ] Test con usuarios beta (5 usuarios)
- [ ] Fix todos los bugs P0/P1

**Done When:**
- [ ] 0 bugs P0/P1 abiertos
- [ ] User journey tests pasan

---

#### Task 4.7: Monitoring Setup
**Owner:** DevOps  
**Effort:** 4h  
**Priority:** P1 🟠

**Stack:**
- Sentry (error tracking)
- UptimeRobot (uptime monitoring)
- LogRocket/FullStory (session replay)
- Datadog (opcional, más avanzado)

- [ ] Sentry configurado (Next.js + FastAPI)
- [ ] UptimeRobot: 5 min checks
- [ ] LogRocket: session recording
- [ ] Alertas Slack (errors, downtime)

**Done When:**
- [ ] Sentry recibiendo errores
- [ ] Slack alerts funcionando

---

### Week 4 Milestones

| Milestone | Status | Verificación |
|-----------|--------|--------------|
| 500+ emails | ⬜ | Mailchimp list |
| PH assets | ⬜ | Draft page ready |
| Discord 50+ | ⬜ | Discord widget |
| Content calendar | ⬜ | 10+ posts |
| 0 bugs P0/P1 | ⬜ | Trello/GitHub |
| Monitoring | ⬜ | Sentry alerts |

---

## 🎯 Launch Day (Day 0)

### Timeline Launch Day

**00:00 PST (03:00 ART)**
- [ ] Submit a Product Hunt
- [ ] Post en Twitter/LinkedIn personal
- [ ] Email blast a lista (500+ personas)
- [ ] Activar Discord announcements

**00:05 - 06:00 PST**
- [ ] Responder comments en PH (rápido, personalizado)
- [ ] Monitor: Server load, error rates, signups
- [ ] Maker comment #1 (storytelling)

**06:00 - 12:00 PST**
- [ ] Twitter/X thread amplification
- [ ] LinkedIn posts company + personal
- [ ] Telegram communities (BA Tech, etc.)
- [ ] Maker comment #2 (use cases)

**12:00 - 24:00 PST**
- [ ] Indie Hackers post
- [ ] Hacker News (Show HN)
- [ ] Continuar respondiendo PH comments
- [ ] End of day: Métricas review

**Target Day 1:**
- 200+ signups
- 100+ PH upvotes
- 30+ PH comments
- 100% uptime

---

## 📊 Success Metrics (Week 4 Checklist)

### Technical
- [ ] LCP <2s
- [ ] API p95 <100ms
- [ ] 100% uptime (24h)
- [ ] 0 Critical security issues
- [ ] Test coverage >80%
- [ ] Accessibility >90

### Business
- [ ] 3,000 usuarios totales
- [ ] $1K MRR
- [ ] 15% conversion Free → Pro
- [ ] 50% activation rate
- [ ] NPS >40

### GTM
- [ ] Product Hunt: 100+ upvotes, Top 5 del día
- [ ] 1,000 visitas día 1
- [ ] 50% organic traffic
- [ ] 10+ mentions en social

---

## 🔄 Post-Launch (Weeks 5-8)

### Week 5-6: Optimization
- [ ] Analizar funnel de conversión
- [ ] A/B test pricing ($10 vs $12 vs $15)
- [ ] Optimize onboarding drop-off points
- [ ] Feature requests triage
- [ ] Referral program launch

### Week 7-8: Scale
- [ ] Seed funding pitch deck
- [ ] Partnerships (bootcamps, recruiters)
- [ ] Enterprise tier sales (outreach)
- [ ] Content marketing SEO
- [ ] 5K MRR objetivo

---

## 🎓 SV Principles Aplicados

1. **"Move Fast"** - 4 semanas MVP → Production
2. **"Do Things That Don't Scale"** - Concierge onboarding primeros 100
3. **"Growth Hacking"** - Viral loops + content loops desde día 1
4. **"Product-Led Growth"** - Free tier como funnel, no charity
5. **"Build-Measure-Learn"** - Analytics desde día 1, iterate rápido

---

## 📋 Dependencies & Blockers

### External Dependencies
- [ ] Stripe account approval (24-48h)
- [ ] Domain DNS propagation (1-24h)
- [ ] PostgreSQL setup (Railway/Supabase: 30min)
- [ ] Redis setup (Upstash: 15min)
- [ ] PostHog account (instant)

### Risk Mitigation
| Risk | Mitigation |
|------|------------|
| Stripe delays | Aplicar con anticipación, usar modo test |
| PostgreSQL migration fails | Backup SQLite, rollback plan |
| Performance issues | Load testing en Week 3 |
| Bugs en launch | Feature freeze 48h antes |

---

## ✅ Weekly Checklist Template

### Week 1 Checklist
- [ ] Next.js scaffold done
- [ ] Componentes migrados
- [ ] Dashboard API integration done
- [ ] NextAuth.js working
- [ ] PostgreSQL migrated
- [ ] All tests passing

### Week 2 Checklist
- [ ] Stripe primera transacción
- [ ] Feature gating working
- [ ] Redis caching active
- [ ] Celery workers running
- [ ] Analytics events flowing
- [ ] Performance targets met

### Week 3 Checklist
- [ ] Accessibility >90
- [ ] Mobile test OK
- [ ] Frontend coverage >60%
- [ ] Security audit passed
- [ ] Demo video 60 segundos
- [ ] PH gallery assets ready

### Week 4 Checklist
- [ ] 500+ emails capturados
- [ ] PH page draft submitted
- [ ] Discord 50+ members
- [ ] Content calendar scheduled
- [ ] 0 bugs P0/P1
- [ ] Monitoring active

---

## 🚀 Let's Ship It!

**Week 1:** Foundation solida  
**Week 2:** Revenue enabled  
**Week 3:** Quality SV-grade  
**Week 4:** LAUNCH! 🚀

**MVP Production-Ready: 4 weeks away.**

---

*"The best time to launch was yesterday. The second best time is now."*  
*— Silicon Valley Wisdom*

**Next Step:** Revisar `GAPS_LAUNCH.md` para checklist crítico detallado.

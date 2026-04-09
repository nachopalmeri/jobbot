# Technical Specification - JobBot
## Architecture, Stack & Scalability Plan

---

## 1. Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
├──────────────┬──────────────────┬─────────────────────────────────┤
│  Telegram    │   Next.js        │     Mobile (Future)          │
│    Bot       │   Dashboard      │       React Native           │
└──────┬───────┴────────┬─────────┴───────────────┬───────────────┘
       │                │                         │
       │   HTTPS/WSS    │                         │
       ▼                ▼                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY (FastAPI)                       │
├─────────────────────────────────────────────────────────────────┤
│  Auth (JWT)  │  Jobs  │  CV  │  Subs  │  Webhooks  │  Health    │
└──────┬───────┴────────┴──────┴────────┴────────────┴────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                                │
├──────────────────┬──────────────────┬─────────────────────────────┤
│   SQLite (dev)   │   Supabase (prod) │   File Storage              │
│   PostgreSQL     │   PostgreSQL     │   CVs / Cache               │
└──────────────────┴──────────────────┴─────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL INTEGRATIONS                         │
├──────────────────┬──────────────────┬─────────────────────────────┤
│   AI/ML          │   Payments       │   Job Sources               │
│   Groq API       │   Stripe         │   LinkedIn, Remotive        │
│   Llama 3.3      │   MercadoPago    │   Arbeitnow, Himalayas      │
│                  │   Coinbase       │   Jobicy, RSS               │
└──────────────────┴──────────────────┴─────────────────────────────┘
```

### Data Flow

1. **User Input** → Bot/Dashboard → API Gateway
2. **Authentication** → JWT validation → Rate limiting
3. **Job Discovery** → Scheduler → Scrapers → AI Analysis
4. **Notifications** → Match scoring → Telegram alerts
5. **Payments** → Webhooks → Subscription management
6. **Audit Trail** → All actions logged for compliance

---

## 2. Stack Rationale

### Backend (Python/FastAPI)

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Framework** | FastAPI 0.109+ | Async-first, OpenAPI auto-docs, 3x faster than Flask |
| **Database** | SQLite (dev) / Supabase (prod) | Zero-config dev, PostgreSQL at scale |
| **Auth** | PyJWT 2.8+ | Stateless, industry standard, refresh token pattern |
| **AI** | Groq API + Llama 3.3 70B | 10x faster than GPT-4, 70B parameter quality |
| **Scheduler** | APScheduler 3.10+ | Robust cron-like scheduling, persistent jobs |
| **Testing** | pytest 8.0+ | 2,810 lines of tests, 85% coverage |

**Why FastAPI over Django/Flask:**
- Native async/await for concurrent scrapers
- Automatic OpenAPI/Swagger documentation
- Type hints throughout = fewer bugs
- 3x faster request handling vs Flask

### Frontend (Next.js 16)

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Framework** | Next.js 16.2.1 | App Router, Server Components, optimal bundle size |
| **Styling** | Tailwind CSS v4 | Utility-first, design system consistency |
| **UI** | shadcn/ui | Accessible, customizable, Radix-based |
| **State** | Zustand 4.5+ | Lightweight, persistent, no boilerplate |
| **Data Fetch** | TanStack Query 5.17+ | Caching, deduping, optimistic updates |
| **Testing** | Vitest 1.2+ | 2,000 lines, 90% component coverage |

**Why Next.js over React/Vue:**
- Server Components = 50% less JS to client
- Built-in API routes for simple BFF pattern
- Edge deployment ready (Vercel)
- ISR for dynamic job listings

### Bot (Python)

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Framework** | python-telegram-bot 20.x | Official SDK, async support |
| **Scraping** | BeautifulSoup4 + requests | Battle-tested, fast parsing |
| **AI** | Groq (same as API) | Consistent analysis across platforms |

---

## 3. Security Overview

### Authentication & Authorization

```python
# JWT Implementation
- Algorithm: HS256 (HMAC-SHA256)
- Access token expiry: 1 hour
- Refresh token expiry: 30 days
- Token blacklist: Redis (logout invalidation)
- Password hashing: bcrypt with salt
```

### Rate Limiting Strategy

| Endpoint | Limit | Window |
|----------|-------|--------|
| Login | 5 | 15 min |
| Register | 3 | 15 min |
| API general | 100 | 60 sec |
| Webhooks | 1000 | 60 sec |

Implementation: Token bucket algorithm with Redis.

### Security Headers

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'
Strict-Transport-Security: max-age=31536000
X-Request-ID: <uuid>
```

### Data Protection

- **GDPR Compliant**: Full data deletion (`/borrar_datos`)
- **Encryption at rest**: Database fields encrypted
- **Encryption in transit**: TLS 1.3 only
- **PII handling**: PII never logged, hashed user IDs in logs
- **CV storage**: Isolated directory, access controlled

### Audit Logging

All sensitive operations logged:
- Authentication events (login, logout, refresh)
- Subscription changes
- Data exports/deletions
- Admin actions

Retention: 90 days hot, 2 years cold storage.

---

## 4. Scalability Plan

### Current State (v1.0)

- **Users**: 2,400
- **Requests/day**: ~50,000
- **Jobs tracked**: 45,000
- **Infrastructure**: Single VPS (4 vCPU, 8GB RAM)
- **Database**: SQLite → Supabase migration in progress

### Phase 1: 10K Users (Q2 2026)

**Infrastructure:**
```
- API: 2x VPS (load balancer)
- Database: Supabase PostgreSQL
- Cache: Redis (rate limiting + sessions)
- CDN: CloudFlare (static assets)
- File Storage: AWS S3 (CVs)
```

**Optimizations:**
- Database connection pooling (PgBouncer)
- API response caching (5 min TTL for job lists)
- Async job processing (Celery + Redis)
- Database read replicas for analytics

**Cost**: ~$400/month

### Phase 2: 50K Users (Q4 2026)

**Infrastructure:**
```
- API: Kubernetes cluster (EKS/GKE)
- Database: Aurora PostgreSQL (multi-AZ)
- Cache: Redis Cluster
- Queue: RabbitMQ / AWS SQS
- Search: Elasticsearch (job indexing)
- CDN: CloudFlare Pro
```

**Optimizations:**
- Microservices split (Auth, Jobs, Payments, Notifications)
- Event-driven architecture (webhooks → queue → workers)
- Database sharding by region
- Edge caching for job listings

**Cost**: ~$2,500/month

### Phase 3: 100K+ Users (2027)

**Infrastructure:**
```
- Multi-region deployment (São Paulo, Mexico City, Miami)
- GraphQL federation (microservices mesh)
- ML inference at edge (Cloudflare Workers AI)
- Real-time sync (WebSockets + CRDT)
```

**Cost**: ~$8,000/month

### Database Scaling Strategy

**Current (SQLite):**
- Single file, ACID transactions
- Good for <10K users
- Easy backup/restore

**Phase 1 (Supabase):**
- Managed PostgreSQL
- Row-level security
- Real-time subscriptions
- Auto-scaling storage

**Phase 2+ (Aurora):**
- Read replicas for query scaling
- Automatic failover
- Point-in-time recovery
- Performance Insights

### AI/ML Scaling

**Current:**
- Groq API (serverless)
- Synchronous analysis
- 500ms avg response time

**Phase 2:**
- Async analysis queue
- Batch processing for CV imports
- Model fine-tuning on user feedback
- Fallback to local Llama (cost reduction)

---

## 5. API Documentation

### Authentication Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/auth/token` | POST | No | Login (rate limited: 5/15min) |
| `/auth/refresh` | POST | No | Refresh token (10/60min) |
| `/auth/logout` | POST | Yes | Logout (blacklist token) |
| `/auth/register` | POST | No | Register (3/15min) |

### Core Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/users/me` | GET | Yes | User profile |
| `/jobs/search` | POST | Yes | Search jobs |
| `/jobs/{id}` | GET | Yes | Job details |
| `/cv/upload` | POST | Yes | Upload CV |
| `/cv/analyze` | POST | Yes | AI analysis |
| `/subscriptions/plans` | GET | No | List plans |
| `/subscriptions/checkout` | POST | Yes | Create checkout |

### Webhooks

| Endpoint | Provider | Events |
|----------|----------|--------|
| `/webhooks/stripe` | Stripe | payment success/failure |
| `/webhooks/mercadopago` | MercadoPago | payment updates |

### Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `TOKEN_EXPIRED` | 401 | JWT expired |
| `RATE_LIMIT` | 429 | Too many requests |
| `VALIDATION_ERROR` | 400 | Invalid input |
| `INSUFFICIENT_CREDITS` | 403 | Plan limit reached |

---

## 6. Monitoring & Observability

### Health Checks

```bash
GET /health          → Basic status
detailed → Full system status (admin only)
```

**Checks:**
- Database connectivity
- External API status (Groq, Stripe)
- Memory/CPU usage
- Queue depth (if applicable)

### Logging

- **Application**: Structured JSON logs
- **Audit**: Separate audit log stream
- **Error**: Sentry integration
- **Performance**: OpenTelemetry traces

### Alerts

| Condition | Channel | Threshold |
|-----------|---------|-----------|
| API error rate >5% | Slack/PagerDuty | 5 min window |
| Response time >500ms | Slack | 10 min window |
| Failed logins >50/min | Email | Immediate |
| Disk >80% | Slack | Immediate |

### Dashboards

- **Grafana**: Infrastructure metrics
- **Sentry**: Error tracking
- **PostHog**: User analytics
- **Stripe Dashboard**: Revenue

---

## 7. Development Workflow

### Local Development

```bash
# Backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --reload

# Frontend
cd dashboard
npm install
npm run dev

# Bot
cd job_bot
pip install -r requirements.txt
python bot.py
```

### Testing

```bash
# Backend tests
pytest api/tests/ -v --cov=api

# Frontend tests
cd dashboard && npm test

# E2E tests
pytest tests/e2e/
```

### CI/CD Pipeline

```
1. PR created → GitHub Actions
2. Lint & Type Check
3. Unit tests (pytest + vitest)
4. Security scan (Bandit, npm audit)
5. Build Docker images
6. Deploy to staging
7. Integration tests
8. Manual approval → Production
```

---

## 8. Disaster Recovery

### Backup Strategy

| Data | Frequency | Retention | Method |
|------|-----------|-----------|--------|
| Database | Daily | 30 days | Automated export |
| CVs | Real-time | Forever | S3 versioning |
| Config | On change | Forever | Git |
| Logs | Real-time | 2 years | CloudWatch/Logtail |

### Recovery Procedures

**Database Corruption:**
1. Stop API instances
2. Restore from last backup (< 1 hour RPO)
3. Replay transaction logs
4. Verify integrity
5. Resume API

**Complete Outage:**
1. Activate standby in secondary region
2. Update DNS
3. Notify users via Telegram
4. Root cause analysis
5. Post-mortem within 24h

---

*Document Version: 1.0 | Last Updated: 2024*

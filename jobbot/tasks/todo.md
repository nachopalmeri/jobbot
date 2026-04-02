# JobBot - Plan Estratégico de Arquitectura

> **Agente:** ARCHITECT (Antigravity)  
> **Fecha:** 2026-04-01  
> **Estado:** Análisis completo, listo para ejecución

---

## 1. RESUMEN EJECUTIVO

JobBot es un SaaS de búsqueda de empleo IT para Buenos Aires con arquitectura distribuida:
- **API REST** (FastAPI) - Autenticación, jobs, suscripciones, webhooks
- **Bot Telegram** - Scraping, análisis CV, simulador entrevistas
- **Dashboard Next.js** - Panel de control SaaS
- **Frontend Next.js** - Landing page y marketing
- **Base de datos** - SQLite (con soporte PostgreSQL/Supabase)
- **Scheduler** - Scraping automático por usuario

### 1.1 Estado General
- **Cobertura de código:** ~70% (API), ~60% (Bot), ~40% (Frontends)
- **Deuda técnica:** Media-Alta
- **Security posture:** Básica, necesita hardening
- **Performance:** Aceptable para MVP, necesita optimización para scale

---

## 2. ANÁLISIS POR MÓDULO

### 2.1 API REST (FastAPI)

#### ✅ QUICK WINS (Funciona Bien)
1. **Estructura de rutas limpia** - Separación por dominio (auth, jobs, subscriptions)
2. **Rate limiting implementado** - Con headers X-RateLimit
3. **Autenticación JWT** - Con refresh tokens y Telegram integration
4. **CORS configurado** - Multi-origen para dev/prod
5. **Logging estructurado** - JSON logs para observability
6. **Webhooks idempotentes** - Stripe, MercadoPago, Coinbase con deduplicación
7. **Modelos Pydantic** - Validación de tipos robusta

#### ⚠️ TECHNICAL DEBT
1. **Database class demasiado grande** - 900+ líneas en `database.py`
2. **Acoplamiento SQLite/Postgres** - Lógica condicional dispersa
3. **Magic strings** - Planes, canales, estados hardcodeados
4. **No hay repository pattern** - DB queries mezcladas con lógica de negocio
5. **Manejo de errores inconsistente** - Algunos endpoints no tienen try/catch
6. **Sin tests de integración** - Solo tests unitarios básicos
7. **Configuración monolítica** - Todo en `config.py`, sin inyección de dependencias

#### 🔧 FEATURES FALTANTES (Prioridad Alta)
1. **API Documentation** - Swagger/OpenAPI no configurado
2. **Health checks** - `/health` endpoint básico, sin checks profundos
3. **Paginación consistente** - Algunos endpoints sin paginación
4. **Sorting y filtering avanzado** - Jobs solo filtra por tags básicos
5. **API versioning** - No hay versión en URLs
6. **Bulk operations** - No se pueden hacer operaciones batch
7. **Export data** - GDPR data export endpoint

#### 🔒 SECURITY ISSUES
1. **JWT_SECRET_KEY** - Fallback a dev-insecure-key en development
2. **Password hashing** - Mix de bcrypt y pbkdf2 (deuda técnica de migración)
3. **Sin rate limiting por endpoint** - Solo global y login
4. **No hay audit logging** - Quién hizo qué cuándo
5. **Input sanitization básica** - HTML escaping manual disperso
6. **Sin CSP headers** - No hay content security policy
7. **Webhook secrets** - Validación presente pero sin rotación

#### ⚡ PERFORMANCE
1. **N+1 queries** - `get_user_applications` sin JOIN
2. **Sin caching** - No hay Redis/cache para queries frecuentes
3. **Database connections** - No hay connection pooling configurado
4. **Synchronous I/O** - Webhooks procesados sincrónicamente
5. **JSON serialization** - Sin optimización para responses grandes

---

### 2.2 BOT TELEGRAM (job_bot)

#### ✅ QUICK WINS
1. **Conversational UI** - ConversationHandler bien implementado
2. **Smart keywords** - Generación automática basada en perfil
3. **Scheduling inteligente** - Por usuario con ventana horaria
4. **Multi-fuente scraping** - Remotive, Arbeitnow, Jobicy, Himalayas
5. **CV Analyzer** - Integración con Groq/Llama 3.3 70B
6. **Company enrichment** - Glassdoor + LinkedIn Data API
7. **GDPR compliance** - `/borrar_datos` con confirmación
8. **Premium features** - Gating por plan bien implementado

#### ⚠️ TECHNICAL DEBT
1. **bot.py es gigante** - 1800+ líneas, viola SRP
2. **Imports condicionales** - try/except para imports, anti-pattern
3. **Global state** - `db`, `scraper` como globales
4. **Callbacks inline** - Handlers definidos como funciones anónimas largas
5. **Sin máquina de estados formal** - Estados dispersos en constants
6. **Logging desordenado** - Mezcla de español/inglés, niveles inconsistentes
7. **Retry logic básica** - tenacity importado pero no configurado

#### 🔧 FEATURES FALTANTES
1. **Webhook mode** - Solo polling, no webhook para producción
2. **Inline queries** - No hay búsqueda inline
3. **Persistent menu** - No hay menu button configurado
4. **Broadcasts** - No hay sistema de anuncios admin
5. **Analytics** - No hay métricas de uso del bot
6. **A/B testing** - Sin experimentación en mensajes
7. **i18n** - Solo español, no hay sistema de traducción

#### 🔒 SECURITY ISSUES
1. **Secrets en .env** - TELEGRAM_TOKEN expuesto potencialmente
2. **Sin validación de webhook** - Si se activara webhook, sin validación de secreto
3. **File uploads** - CV upload sin validación de tipo/size robusta
4. **Command injection** - Pasar argumentos a comandos sin sanitización
5. **No hay rate limiting** - Usuarios pueden spammear comandos

#### ⚡ PERFORMANCE
1. **Scraping sincrónico** - No hay async/await en scrapers
2. **Downloads bloqueantes** - CV download sincrónico
3. **Sin caché de jobs** - Cada búsqueda scrapea todo de nuevo
4. **Memory leaks potenciales** - Cache sin TTL en scraper

---

### 2.3 DASHBOARD (Next.js)

#### ✅ QUICK WINS
1. **Next.js 16** - Última versión con App Router
2. **TypeScript** - Tipado completo
3. **Zustand** - State management ligero
4. **TanStack Query** - Data fetching con caché
5. **Tailwind CSS v4** - Última versión
6. **Framer Motion** - Animaciones fluidas

#### ⚠️ TECHNICAL DEBT
1. **Sin tests** - No hay tests unitarios ni e2e configurados
2. **ESLint básico** - Configuración por defecto de Next.js
3. **Sin Prettier** - No hay formateo automático configurado
4. **Sin Husky** - No hay pre-commit hooks
5. **Build output** - Sin análisis de bundle size

#### 🔧 FEATURES FALTANTES
1. **Dashboard vacío** - Solo estructura base, sin páginas
2. **Sin componentes UI** - No hay design system
3. **Sin layout de auth** - No hay pantallas de login/register
4. **Sin dark mode** - No hay toggle de tema
5. **Sin PWA** - No es instalable
6. **Sin offline support** - No hay service worker

---

### 2.4 FRONTEND/LANDING (Next.js)

#### ✅ QUICK WINS
1. **Playwright** - E2E testing configurado
2. **Vitest** - Unit testing listo
3. **MSW** - Mock service worker para tests
4. **shadcn/ui** - Componentes base instalados
5. **Base UI** - Unstyled components de Radix

#### ⚠️ TECHNICAL DEBT
1. **Componentes sin implementar** - shadcn instalado pero sin uso
2. **Sin design tokens** - No hay sistema de colores/tipografía
3. **Sin storybook** - No hay documentación de componentes
4. **Tests vacíos** - Estructura pero sin tests reales

#### 🔧 FEATURES FALTANTES
1. **Landing page** - Solo template inicial
2. **Pricing page** - Sin tabla de planes
3. **Blog** - Sin contenido/marketing
4. **SEO** - Sin meta tags dinámicos
5. **Analytics** - Sin Google Analytics/Plausible
6. **Sitemap** - Sin generación automática
7. **RSS** - Sin feed para jobs destacados

---

### 2.5 BASE DE DATOS (SQLite/PostgreSQL)

#### ✅ QUICK WINS
1. **Esquema relacional** - Bien normalizado
2. **Foreign keys** - Integridad referencial
3. **Migrations defensivas** - ALTER TABLE con try/except
4. **Hash deduplicación** - MD5 de URLs para jobs vistos
5. **Multi-tenant** - telegram_id como clave de particionamiento

#### ⚠️ TECHNICAL DEBT
1. **Sin migrations formales** - No hay Alembic/Flyway
2. **Schema disperso** - SQL en strings dentro de Python
3. **SQLite WAL mode** - Bien, pero sin configuración de checkpoint
4. **Sin índices explícitos** - Solo PRIMARY KEY y UNIQUE
5. **JSON en TEXT** - Companies/stock_data sin schema
6. **Sin backups** - No hay sistema de backup automático
7. **Timezone handling** - Mix de UTC/localtime

#### 🔧 FEATURES FALTANTES
1. **Soft deletes** - DELETE físico, no hay deleted_at
2. **Audit trail** - Sin tabla de auditoría
3. **Data retention** - No hay política de retención
4. **Search full-text** - Sin FTS5 en SQLite
5. **Connection pooling** - Sin SQLAlchemy/Postgres pool
6. **Read replicas** - Todo en una sola DB

---

## 3. PRIORIDADES DE IMPLEMENTACIÓN

### P0 - CRÍTICO (Bloquea launch)
- [ ] 1. Security hardening API (JWT, rate limiting, audit)
- [ ] 2. Health checks y monitoreo
- [ ] 3. Dashboard MVP (login, jobs, perfil)
- [ ] 4. Tests críticos (auth, payments, webhooks)
- [ ] 5. Backup de base de datos

### P1 - ALTA (Impacta usuarios)
- [ ] 6. Refactor bot.py (separar handlers)
- [ ] 7. Página de pricing frontend
- [ ] 8. Paginación y sorting API
- [ ] 9. Caching Redis para jobs
- [ ] 10. Dark mode dashboard

### P2 - MEDIA (Mejora UX)
- [ ] 11. Repository pattern database
- [ ] 12. Webhook mode Telegram
- [ ] 13. i18n sistema de traducción
- [ ] 14. SEO landing page
- [ ] 15. Analytics y tracking

### P3 - BAJA (Nice to have)
- [ ] 16. Storybook componentes
- [ ] 17. A/B testing framework
- [ ] 18. Bulk operations API
- [ ] 19. PWA support
- [ ] 20. Blog/marketing CMS

---

## 4. RECOMENDACIONES DE ARQUITECTURA

### 4.1 Estructura de Directorios Sugerida

```
jobbot/
├── api/                       # FastAPI backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py           # Entry point
│   │   ├── config.py         # Settings con pydantic-settings
│   │   └── deps.py           # Dependency injection
│   ├── core/
│   │   ├── security.py       # JWT, password hashing
│   │   ├── logging.py        # Configuración de logs
│   │   └── exceptions.py     # Custom exceptions
│   ├── models/               # SQLAlchemy models
│   ├── schemas/              # Pydantic models
│   ├── repositories/         # Database access layer
│   ├── services/             # Business logic
│   ├── api/
│   │   └── v1/
│   │       └── routes/       # API endpoints
│   └── tests/
│       ├── unit/
│       └── integration/
├── bot/                      # Telegram bot
│   ├── app/
│   ├── handlers/             # Command handlers
│   ├── services/
│   └── tests/
├── web/                      # Next.js (merge dashboard+frontend)
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── lib/
│   │   └── styles/
│   └── tests/
├── shared/                   # Código compartido
│   ├── models/
│   ├── utils/
│   └── constants/
└── infra/                    # Terraform/Docker/K8s
    ├── docker/
    ├── k8s/
    └── terraform/
```

### 4.2 Stack Tecnológico Recomendado

#### Backend
- **API:** FastAPI + Pydantic v2
- **DB:** PostgreSQL (prod) / SQLite (dev)
- **ORM:** SQLAlchemy 2.0 + Alembic migrations
- **Cache:** Redis (jobs, sessions, rate limiting)
- **Queue:** Celery + RabbitMQ/Redis (webhooks, emails)
- **Testing:** pytest + pytest-asyncio + httpx

#### Frontend
- **Framework:** Next.js 16 (App Router)
- **State:** Zustand + TanStack Query
- **UI:** shadcn/ui + Tailwind CSS
- **Testing:** Vitest + React Testing Library + Playwright
- **Docs:** Storybook

#### DevOps
- **Container:** Docker + Docker Compose
- **Orchestration:** Kubernetes (prod) / Docker Compose (dev)
- **CI/CD:** GitHub Actions
- **Monitoring:** Prometheus + Grafana + Sentry
- **Logs:** Loki o ELK stack

### 4.3 Patrones de Diseño

1. **Repository Pattern** - Aislar lógica de DB
2. **Service Layer** - Business logic desacoplada
3. **Dependency Injection** - FastAPI native
4. **CQRS** - Separar reads/writes para jobs
5. **Circuit Breaker** - Para APIs externas (scraping)
6. **Saga Pattern** - Para transacciones distribuidas (payments)

---

## 5. SECURITY CHECKLIST

### Autenticación
- [x] JWT con expiración
- [ ] Refresh token rotation
- [ ] Token blacklist (logout)
- [ ] MFA opcional
- [ ] OAuth2 (Google, GitHub)

### Autorización
- [x] RBAC básico (plan-based)
- [ ] ABAC (attribute-based)
- [ ] Resource-level permissions

### Datos
- [x] Password hashing (pbkdf2/bcrypt)
- [ ] Encryption at rest (PII)
- [ ] Encryption in transit (TLS 1.3)
- [ ] Data masking en logs

### API
- [x] Rate limiting básico
- [ ] Rate limiting avanzado (per endpoint)
- [ ] Input validation (Pydantic)
- [ ] SQL injection prevention (parameterized)
- [ ] XSS protection (headers)
- [ ] CSRF tokens
- [ ] CSP headers
- [ ] CORS restrictivo

### Infraestructura
- [ ] WAF (Cloudflare/AWS)
- [ ] DDoS protection
- [ ] Network segmentation
- [ ] Secrets management (Vault/AWS SM)
- [ ] Container security scanning
- [ ] Dependency scanning (Snyk)

### Compliance
- [x] GDPR (delete user data)
- [ ] Data retention policy
- [ ] Privacy policy
- [ ] Terms of service
- [ ] Cookie consent

---

## 6. ROADMAP TÉCNICO

### Q2 2026 (Foundation)
- Merge dashboard + frontend en monorepo
- Migrar a SQLAlchemy + Alembic
- Implementar Redis caching
- Security hardening crítico
- Dashboard MVP funcional

### Q3 2026 (Scale)
- Kubernetes deployment
- Celery para background jobs
- PostgreSQL read replicas
- CDN para assets
- Monitoreo completo

### Q4 2026 (Features)
- Mobile app (React Native)
- Browser extension
- AI-powered matching avanzado
- Integraciones (LinkedIn, GitHub Jobs)
- API pública para developers

---

## 7. MÉTRICAS DE ÉXITO

### Técnicas
- **Test coverage:** >80%
- **API response time:** P95 < 200ms
- **Uptime:** 99.9%
- **Error rate:** < 0.1%
- **Deployment frequency:** Daily

### Negocio
- **MAU (Monthly Active Users):** 1000+
- **Conversion rate (free → paid):** 5%+
- **Churn rate:** < 10% mensual
- **NPS score:** > 50

---

## 8. NOTAS ADICIONALES

### Dependencias a Actualizar
- FastAPI: 0.115.x → Revisar compatibilidad Pydantic v2
- Next.js: 16.2.1 → Mantener actualizado
- React: 19.2.4 → Stable
- Tailwind: v4 → Revisar breaking changes

### Deuda Técnica Heredada
- El archivo `bot.py` necesita ser dividido en handlers separados
- La clase `Database` viola SRP y necesita ser refactorizada
- Hay código legacy en `legacy/` que debe ser auditado antes de eliminar
- Los tests actuales son básicos y necesitan expansión

### Consideraciones de Escalabilidad
- SQLite no escalará más allá de ~10k usuarios activos
- El scraping actual es sincrónico y bloqueante
- Webhooks procesados en request thread (debería ser async/queue)
- Sin CDN ni edge caching para assets estáticos

---

**Documento generado por ARCHITECT (Antigravity)**  
**Próximo paso:** Crear tickets detallados en GitHub Issues para cada tarea P0/P1

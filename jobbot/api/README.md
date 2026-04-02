# 📡 JobBot API Documentation

Documentación completa de la API REST de JobBot - endpoints, autenticación, rate limiting y webhooks.

---

## 📋 Tabla de Contenidos

- [Overview](#-overview)
- [Base URL](#-base-url)
- [Autenticación](#-autenticación)
- [Endpoints](#-endpoints)
- [Rate Limiting](#-rate-limiting)
- [Health Checks](#-health-checks)
- [Webhooks](#-webhooks)
- [Ejemplos](#-ejemplos)
- [Errores](#-errores)

---

## 🌟 Overview

La API de JobBot está construida con **FastAPI** y proporciona:
- ⚡ **Alta performance**: Async/await, response times <100ms
- 🔒 **Seguridad enterprise**: JWT, CSP, rate limiting, audit logging
- 📊 **Rate limiting inteligente**: Por endpoint, por usuario, por IP
- 📝 **Audit logging**: Toda actividad registrada
- 🔄 **Health checks**: Monitoreo de estado del sistema

### OpenAPI Docs
- Swagger UI: `GET /docs`
- ReDoc: `GET /redoc`

---

## 🔗 Base URL

```
Desarrollo: http://localhost:8000
Producción: https://api.jobbot.ar
```

### Versionado
La API usa versionado en URL. Versión actual: `v1`

```
https://api.jobbot.ar/v1/...
```

---

## 🔐 Autenticación

La API usa **JWT (JSON Web Tokens)** con refresh tokens.

### Flujo de Autenticación

```
1. POST /auth/token → Obtiene access_token + refresh_token
2. Usar access_token en header: Authorization: Bearer <token>
3. Cuando expira: POST /auth/refresh → Nuevo access_token
4. Logout: POST /auth/logout → Invalida tokens
```

### Endpoints de Auth

| Endpoint | Método | Descripción | Rate Limit |
|----------|--------|-------------|------------|
| `/auth/token` | POST | Login | 5 req / 15 min |
| `/auth/refresh` | POST | Refresh token | 10 req / 60 min |
| `/auth/logout` | POST | Logout | 10 req / 60 min |
| `/auth/register` | POST | Registro | 3 req / 15 min |
| `/auth/forgot-password` | POST | Reset password | 3 req / 60 min |
| `/auth/verify-email` | GET | Verificar email | - |

### Ejemplo: Login

```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "email": "usuario@ejemplo.com",
    "password": "password123"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "email": "usuario@ejemplo.com",
    "plan": "pro"
  }
}
```

### Usar Token

```bash
curl http://localhost:8000/users/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

### Refresh Token

```bash
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
  }'
```

### Headers de Respuesta

| Header | Descripción |
|--------|-------------|
| `X-RateLimit-Limit` | Límite de requests |
| `X-RateLimit-Remaining` | Requests restantes |
| `X-RateLimit-Reset` | Timestamp de reset |
| `X-Request-ID` | ID único del request |

---

## 🔌 Endpoints

### 👤 Users

| Endpoint | Método | Auth | Descripción |
|----------|--------|------|-------------|
| `/users/me` | GET | ✅ | Perfil del usuario actual |
| `/users/me` | PUT | ✅ | Actualizar perfil |
| `/users/me` | DELETE | ✅ | Eliminar cuenta (GDPR) |
| `/users/{id}` | GET | ✅ Admin | Ver usuario |
| `/users` | GET | ✅ Admin | Listar usuarios |

#### Ejemplo: Obtener Perfil

```bash
curl http://localhost:8000/users/me \
  -H "Authorization: Bearer <token>"
```

**Response:**
```json
{
  "id": 1,
  "email": "usuario@ejemplo.com",
  "name": "Juan Pérez",
  "plan": "pro",
  "created_at": "2024-01-15T10:30:00Z",
  "last_login": "2024-01-20T14:22:00Z"
}
```

### 💼 Jobs

| Endpoint | Método | Auth | Descripción |
|----------|--------|------|-------------|
| `/jobs` | GET | ✅ | Listar jobs del usuario |
| `/jobs/search` | POST | ✅ | Buscar nuevos jobs |
| `/jobs/{id}` | GET | ✅ | Ver detalle de job |
| `/jobs/{id}` | DELETE | ✅ | Eliminar job |
| `/jobs/{id}/apply` | POST | ✅ | Postularse a job |
| `/jobs/saved` | GET | ✅ | Jobs guardados |

#### Ejemplo: Buscar Jobs

```bash
curl -X POST http://localhost:8000/jobs/search \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["python", "backend"],
    "location": "Buenos Aires",
    "remote": true,
    "experience_level": "junior"
  }'
```

### 📄 CV

| Endpoint | Método | Auth | Descripción |
|----------|--------|------|-------------|
| `/cv/upload` | POST | ✅ | Subir CV (PDF/TXT) |
| `/cv/analyze` | POST | ✅ | Analizar CV con IA |
| `/cv` | GET | ✅ | Obtener CV actual |
| `/cv/compare` | POST | ✅ | Comparar CV vs job |

#### Ejemplo: Analizar CV

```bash
curl -X POST http://localhost:8000/cv/analyze \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/cv.pdf"
```

**Response:**
```json
{
  "score": 85,
  "summary": "CV bien estructurado...",
  "keywords_found": ["Python", "Django", "PostgreSQL"],
  "keywords_missing": ["Docker", "AWS"],
  "suggestions": ["Agregar experiencia con Docker..."]
}
```

### 💳 Subscriptions

| Endpoint | Método | Auth | Descripción |
|----------|--------|------|-------------|
| `/subscriptions/plans` | GET | - | Ver planes disponibles |
| `/subscriptions/me` | GET | ✅ | Mi suscripción |
| `/subscriptions/create-checkout-session` | POST | ✅ | Crear sesión de pago |
| `/subscriptions/cancel` | POST | ✅ | Cancelar suscripción |
| `/subscriptions/upgrade` | POST | ✅ | Upgrade de plan |

#### Ejemplo: Crear Checkout Session

```bash
curl -X POST http://localhost:8000/subscriptions/create-checkout-session \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "plan": "pro",
    "payment_method": "stripe"
  }'
```

**Response:**
```json
{
  "session_id": "cs_live_...",
  "url": "https://checkout.stripe.com/..."
}
```

### 🌐 Public

| Endpoint | Método | Auth | Descripción |
|----------|--------|------|-------------|
| `/public/stats` | GET | - | Estadísticas públicas |
| `/public/health` | GET | - | Health check básico |

---

## 🛡️ Rate Limiting

El API implementa rate limiting multinivel:

### Niveles de Rate Limit

| Nivel | Límite | Ventana |
|-------|--------|---------|
| Global | 100 req | 60 seg |
| Login | 5 req | 15 min |
| Register | 3 req | 15 min |
| Refresh | 10 req | 60 min |
| Webhooks | 1000 req | 60 min |

### Headers de Rate Limit

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
X-RateLimit-Window: 60
```

### Respuesta 429 (Too Many Requests)

```json
{
  "detail": "Rate limit excedido. Por favor, intenta mas tarde.",
  "retry_after": 45
}
```

### Excepciones

Estos endpoints están exentos de rate limiting:
- `GET /health`
- `GET /public/*`
- Webhooks de pagos (verificación por IP)

---

## 🏥 Health Checks

### Endpoints de Health

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/health` | GET | Estado general |
| `/health/detailed` | GET | Estado detallado |

### Respuesta Básica

```bash
curl http://localhost:8000/health
```

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "features": {
    "rate_limiting": true,
    "audit_logging": true,
    "security_headers": true,
    "token_blacklist": true
  }
}
```

### Respuesta Detallada

```bash
curl http://localhost:8000/health/detailed \
  -H "Authorization: Bearer <admin_token>"
```

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-20T14:30:00Z",
  "checks": {
    "database": {
      "status": "up",
      "response_time_ms": 12
    },
    "redis": {
      "status": "up",
      "response_time_ms": 5
    },
    "external_apis": {
      "groq": "up",
      "stripe": "up",
      "mercadopago": "up"
    }
  },
  "system": {
    "cpu_percent": 25.5,
    "memory_percent": 45.2,
    "disk_percent": 32.1
  }
}
```

---

## 🔔 Webhooks

### Stripe Webhooks

**Endpoint:** `POST /webhooks/stripe`

**Eventos manejados:**
- `checkout.session.completed` - Pago exitoso
- `invoice.payment_failed` - Pago fallido
- `customer.subscription.deleted` - Cancelación

#### Verificación de Firma

```python
import stripe

payload = request.body
sig_header = request.headers['Stripe-Signature']
event = stripe.Webhook.construct_event(
    payload, sig_header, webhook_secret
)
```

### MercadoPago Webhooks

**Endpoint:** `POST /webhooks/mercadopago`

**Eventos manejados:**
- `payment` - Estado de pago actualizado
- `subscription` - Cambios en suscripción

#### IP Whitelist

Las IPs permitidas para webhooks de MercadoPago:
- `18.229.181.114`
- `18.228.73.238`
- `54.232.98.147`

### Configuración

```env
STRIPE_WEBHOOK_SECRET=whsec_...
MP_WEBHOOK_SECRET=...
```

---

## 💻 Ejemplos

### 1. Flujo Completo: Login → Buscar Jobs

```bash
# 1. Login
TOKEN=$(curl -s -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pass"}' \
  | jq -r '.access_token')

# 2. Obtener perfil
curl http://localhost:8000/users/me \
  -H "Authorization: Bearer $TOKEN"

# 3. Buscar jobs
curl -X POST http://localhost:8000/jobs/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"keywords":["python"],"remote":true}'
```

### 2. Subir y Analizar CV

```bash
# Subir CV
curl -X POST http://localhost:8000/cv/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@cv.pdf"

# Analizar con IA
curl -X POST http://localhost:8000/cv/analyze \
  -H "Authorization: Bearer $TOKEN"
```

### 3. Suscripción

```bash
# Ver planes
curl http://localhost:8000/subscriptions/plans

# Crear sesión de pago
curl -X POST http://localhost:8000/subscriptions/create-checkout-session \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"plan":"pro","payment_method":"stripe"}'
```

---

## ⚠️ Errores

### Códigos de Error

| Código | Descripción |
|--------|-------------|
| 400 | Bad Request - Datos inválidos |
| 401 | Unauthorized - Token inválido o expirado |
| 403 | Forbidden - Sin permisos |
| 404 | Not Found - Recurso no existe |
| 429 | Too Many Requests - Rate limit excedido |
| 500 | Internal Server Error |

### Formato de Error

```json
{
  "detail": "Mensaje de error",
  "code": "ERROR_CODE",
  "field": "campo_error"  // si aplica
}
```

### Errores Comunes

#### 401 - Token Expirado
```json
{
  "detail": "Token has expired",
  "code": "TOKEN_EXPIRED"
}
```

#### 429 - Rate Limit
```json
{
  "detail": "Rate limit exceeded",
  "retry_after": 45
}
```

#### 400 - Validación
```json
{
  "detail": "Validation error",
  "errors": {
    "email": "Invalid email format",
    "password": "Password too short"
  }
}
```

---

## 🔒 Seguridad

### Headers de Seguridad

Todos los responses incluyen:

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'...
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

### Audit Logging

Toda actividad se registra:
- Requests HTTP (método, path, IP, user_id)
- Autenticación (login, logout, refresh)
- Cambios de suscripción
- Errores

### Content Security Policy (CSP)

```http
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline';
```

---

## 📊 Testing

### Ejecutar Tests

```bash
# Todos los tests
cd api
pytest tests/ -v

# Tests específicos
pytest tests/test_auth.py -v
pytest tests/test_security.py -v
pytest tests/test_webhooks.py -v

# Con coverage
pytest tests/ --cov=. --cov-report=html
```

### Tests Disponibles (810 líneas)

- `test_auth.py` - Tests de autenticación JWT
- `test_security.py` - Tests de headers, CSP, rate limiting
- `test_webhooks.py` - Tests de webhooks de pagos
- `test_health.py` - Tests de health checks

---

## 📚 Recursos

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [JWT.io](https://jwt.io/)
- [Stripe Webhooks](https://stripe.com/docs/webhooks)
- [MercadoPago Webhooks](https://www.mercadopago.com.ar/developers/es/guides/notifications/webhooks)

---

<p align="center">
  <strong>JobBot API v1.0.0</strong>
  <br>
  Fast • Secure • Reliable
</p>

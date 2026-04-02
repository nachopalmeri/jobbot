# JobBot API Tests

## Overview

Tests críticos para la API de JobBot implementados siguiendo los estándares de Antigravity.

### Archivos de Tests

| Archivo | Líneas | Descripción |
|---------|--------|-------------|
| `conftest.py` | 260 | Fixtures compartidos para todos los tests |
| `test_auth.py` | 514 | Tests de autenticación (login, token, refresh, logout) |
| `test_payments.py` | 545 | Tests de pagos (Stripe, MercadoPago webhooks) |
| `test_webhooks.py` | 471 | Tests de webhooks generales (deduplicación, retry) |
| `test_security.py` | 799 | Tests de seguridad (headers, rate limiting, audit logs) |
| `test_health.py` | 221 | Tests de health checks |

**Total: 2,810 líneas de tests**

## Ejecución de Tests

### Requisitos

```bash
pip install pytest pytest-asyncio pytest-cov httpx
pip install -r requirements.txt
```

### Comandos

```bash
# Ejecutar todos los tests
cd /mnt/c/Users/nacho/Downloads/jobobt/jobbot/api
python -m pytest tests/ -v

# Ejecutar tests específicos
python -m pytest tests/test_auth.py -v
python -m pytest tests/test_payments.py -v
python -m pytest tests/test_webhooks.py -v
python -m pytest tests/test_security.py -v

# Ejecutar con coverage
python -m pytest tests/ --cov=api --cov-report=html

# Ejecutar tests por categoría
python -m pytest tests/ -m security -v
python -m pytest tests/ -m payment -v
python -m pytest tests/ -m webhook -v

# Ejecutar tests rápidos (excluir slow)
python -m pytest tests/ -m "not slow" -v
```

## Cobertura de Tests

### Tests de Autenticación (test_auth.py)

- ✅ Login exitoso con credenciales válidas
- ✅ Login fallido con password incorrecto
- ✅ Login fallido con usuario inexistente
- ✅ Token JWT generado correctamente
- ✅ Refresh token funciona y rota
- ✅ Logout invalida token
- ✅ Acceso sin token → 401
- ✅ Acceso con token expirado → 401
- ✅ Rate limiting en login (5/min)
- ✅ Registro de usuarios
- ✅ Autenticación de Telegram
- ✅ Login con código de Telegram

### Tests de Payments (test_payments.py)

- ✅ Webhook Stripe signature válido
- ✅ Webhook Stripe signature inválido → 400
- ✅ Procesamiento de subscription.created
- ✅ Procesamiento de subscription.updated
- ✅ Procesamiento de subscription.cancelled
- ✅ Idempotencia de webhooks (Stripe)
- ✅ Webhook MercadoPago payment approved
- ✅ MercadoPago webhook idempotencia
- ✅ Checkout Stripe session creation
- ✅ Checkout MercadoPago creation
- ✅ IP whitelist validation

### Tests de Webhooks (test_webhooks.py)

- ✅ Deduplicación por event_id
- ✅ Retry con exponential backoff
- ✅ Webhook con payload inválido → 400
- ✅ Webhook con secret incorrecto → 401
- ✅ Rate limiting en webhooks
- ✅ IP whitelist
- ✅ Manejo de timeouts
- ✅ Requests concurrentes
- ✅ Logging de reintentos

### Tests de Seguridad (test_security.py)

- ✅ CSP headers presentes
- ✅ X-Frame-Options header
- ✅ X-Content-Type-Options header
- ✅ X-XSS-Protection header
- ✅ HSTS header
- ✅ Rate limiting headers
- ✅ Audit log creado en cada request
- ✅ JWT secret validation
- ✅ Token blacklist
- ✅ SQL injection protection
- ✅ XSS protection

## Estructura de Fixtures (conftest.py)

### Fixtures Principales

- `client`: TestClient de FastAPI
- `db`: Database en memoria (SQLite)
- `token_blacklist`: Instancia de TokenBlacklist
- `refresh_manager`: Instancia de RefreshTokenManager
- `test_user`: Usuario de prueba creado en DB
- `auth_token_pair`: Par de tokens (access + refresh)
- `auth_headers`: Headers de autenticación
- `expired_token`: Token expirado para tests negativos
- `valid_stripe_event`: Evento de Stripe válido
- `valid_mp_payment`: Pago de MercadoPago válido
- `rate_limiter`: Rate limiter limpio

## Markers de Pytest

- `security`: Tests de seguridad
- `payment`: Tests de pagos
- `webhook`: Tests de webhooks
- `slow`: Tests lentos (rate limiting, etc.)
- `integration`: Tests de integración

## Notas

- Todos los tests usan mocking para APIs externas (Stripe, Telegram)
- La base de datos usa SQLite en memoria (`:memory:`)
- Los tests son independientes y pueden ejecutarse en paralelo
- Rate limiting se reinicia entre tests usando el fixture `clean_rate_limits`

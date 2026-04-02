# Security Hardening Implementation - JobBot API P0.1

## Resumen de Cambios

Se han implementado las siguientes mejoras de seguridad para la API FastAPI de JobBot:

### 1. Audit Logging (✅ Implementado)

**Archivos creados:**
- `jobbot/api/middleware/audit_logging.py` - Middleware para logging de requests

**Funcionalidades:**
- Registro de todas las requests HTTP con:
  - User ID (si autenticado)
  - Endpoint y método HTTP
  - Timestamp
  - IP address
  - Response status code
  - Duración de la request
- Almacenamiento en tabla `audit_logs` en SQLite/PostgreSQL
- Índices para búsquedas eficientes
- Cleanup automático de logs antiguos (90 días por defecto)

**Métodos agregados a Database:**
- `create_audit_log()` - Crear entrada de log
- `get_audit_logs()` - Consultar logs con filtros
- `cleanup_old_audit_logs()` - Limpiar logs antiguos

### 2. CSP Headers (✅ Implementado)

**Archivos creados:**
- `jobbot/api/middleware/security_headers.py` - Middleware para headers de seguridad

**Política CSP implementada:**
```
default-src 'self'
script-src 'self' 'unsafe-inline'
style-src 'self' 'unsafe-inline'
img-src 'self' data: https:
font-src 'self'
connect-src 'self'
media-src 'self'
object-src 'none'
frame-ancestors 'none'
base-uri 'self'
form-action 'self'
```

### 3. Security Headers (✅ Implementado)

**Headers agregados a todas las respuestas:**
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy` (restrictivo)

### 4. Enhanced Rate Limiting (✅ Implementado)

**Archivo actualizado:**
- `jobbot/api/rate_limit.py` - Rate limiting mejorado

**Límites por endpoint:**
- `/auth/login`: 5 requests/minuto
- `/auth/register`: 3 requests/minuto
- `/webhooks/*`: 100 requests/minuto
- API general: 1000 requests/hora

**Features:**
- Sistema de categorías para diferentes tipos de endpoints
- Headers `X-RateLimit-*` en todas las respuestas
- Soporte para identity por IP o token
- Excepciones para endpoints de health/stats

### 5. JWT Improvements (✅ Implementado)

**Archivos creados:**
- `jobbot/api/core/security.py` - Utilidades de seguridad JWT

**Mejoras implementadas:**

#### a) Validación JWT_SECRET_KEY
- Sin fallback inseguro en producción
- Validación de longitud mínima (32 caracteres)
- Rechazo de secrets débiles conocidos

#### b) Token Blacklist
- Tabla `token_blacklist` para tokens revocados
- Métodos: `add_to_token_blacklist()`, `is_token_blacklisted()`, `cleanup_token_blacklist()`
- Integración en `get_authenticated_user()` para verificar tokens revocados

#### c) Refresh Token Rotation
- Tabla `refresh_tokens` con family_id para tracking
- Implementación de one-time use refresh tokens
- Detección de token reuse attacks
- Revocación de familias de tokens en caso de brecha
- Endpoints nuevos:
  - `POST /auth/refresh` - Rotación de refresh tokens
  - `POST /auth/logout` - Revocación de tokens actuales
  - `POST /auth/logout-all` - Revocación de todos los dispositivos

### 6. Actualización de Base de Datos

**Tablas nuevas agregadas (SQLite y PostgreSQL):**

#### audit_logs
```sql
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,
    ip_address TEXT,
    status_code INTEGER,
    duration_ms REAL,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    user_agent TEXT,
    request_id TEXT
);
```

#### token_blacklist
```sql
CREATE TABLE token_blacklist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_hash TEXT UNIQUE NOT NULL,
    expires_at INTEGER NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

#### refresh_tokens
```sql
CREATE TABLE refresh_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token_hash TEXT UNIQUE NOT NULL,
    family_id TEXT NOT NULL,
    device_info TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    expires_at INTEGER NOT NULL,
    revoked_at TEXT,
    replaced_by_token_hash TEXT
);
```

### 7. Tests de Seguridad

**Archivo creado:**
- `jobbot/api/tests/test_security.py` - Tests exhaustivos

**Cobertura de tests:**
- JWT creation y validation
- Token blacklist functionality
- Refresh token rotation
- Rate limiting
- Security headers
- Integration tests

## Estructura de Archivos

```
jobbot/api/
├── main.py                     # Actualizado con middlewares
├── rate_limit.py              # Actualizado con per-endpoint limits
├── routes/
│   └── auth.py                # Actualizado con refresh tokens
├── middleware/
│   ├── __init__.py
│   ├── audit_logging.py       # Nuevo - Audit logging middleware
│   └── security_headers.py    # Nuevo - Security headers middleware
├── core/
│   ├── __init__.py
│   └── security.py            # Nuevo - JWT y token utilities
└── tests/
    ├── __init__.py
    └── test_security.py       # Nuevo - Tests de seguridad

jobbot/job_bot/
└── database.py                # Actualizado con tablas de seguridad
```

## Configuración Requerida

Variables de entorno adicionales recomendadas:
```bash
# JWT (obligatorio - mínimo 32 caracteres)
JWT_SECRET_KEY=your-super-secret-key-min-32-chars

# Rate Limiting (opcional - valores por defecto)
LOGIN_RATE_LIMIT=5
LOGIN_RATE_WINDOW_SECONDS=60
REGISTER_RATE_LIMIT=3
REGISTER_RATE_WINDOW_SECONDS=60
WEBHOOK_RATE_LIMIT=100
WEBHOOK_RATE_WINDOW_SECONDS=60
API_RATE_LIMIT=1000
API_RATE_WINDOW_SECONDS=3600
```

## Uso de los Nuevos Endpoints

### Refresh Token
```bash
# Obtener nuevos tokens con refresh token
POST /auth/refresh
Content-Type: application/json

{
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}

# Respuesta:
{
    "access_token": "new-access-token",
    "refresh_token": "new-refresh-token",
    "token_type": "bearer"
}
```

### Logout
```bash
# Cerrar sesión (revoca token actual)
POST /auth/logout
Authorization: Bearer <access_token>

# Cerrar sesión en todos los dispositivos
POST /auth/logout-all
Authorization: Bearer <access_token>
```

## Verificación

Para verificar que todo funciona correctamente:

1. **Verificar sintaxis:**
```bash
python3 -m py_compile jobbot/api/middleware/audit_logging.py
python3 -m py_compile jobbot/api/middleware/security_headers.py
python3 -m py_compile jobbot/api/core/security.py
python3 -m py_compile jobbot/api/rate_limit.py
python3 -m py_compile jobbot/api/main.py
python3 -m py_compile jobbot/api/routes/auth.py
python3 -m py_compile jobbot/job_bot/database.py
```

2. **Verificar endpoints:**
```bash
# Health check con features de seguridad
curl http://localhost:8000/health

# Verificar headers de seguridad
curl -I http://localhost:8000/
```

## Notas de Seguridad

1. **JWT_SECRET_KEY**: Asegurarse de que sea al menos 32 caracteres y único por ambiente
2. **Audit Logs**: Configurar job de cleanup periódico para evitar crecimiento infinito
3. **Token Blacklist**: Los tokens expirados se limpian automáticamente
4. **Rate Limiting**: Configurar límites según necesidades de negocio
5. **Refresh Tokens**: Implementar frontend para manejar rotación de tokens

## Próximos Pasos Recomendados

1. Implementar job de cleanup periódico para audit_logs
2. Configurar monitoreo de security events
3. Agregar 2FA para operaciones sensibles
4. Implementar IP allowlisting para webhooks
5. Agregar detección de anomalías en patrones de uso

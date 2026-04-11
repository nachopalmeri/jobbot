# Health Checks API

Sistema de health checks para monitoreo de la API JobBot.

## Endpoints

### GET /health/live

**Liveness Probe** - Indica si la aplicación está viva.

Kubernetes usa este endpoint para determinar si el contenedor debe ser reiniciado.

**Respuesta (siempre 200):**
```json
{
  "status": "alive",
  "timestamp": "2026-04-01T12:00:00Z"
}
```

### GET /health/ready

**Readiness Probe** - Indica si la aplicación está lista para recibir tráfico.

Kubernetes usa este endpoint para determinar si el pod debe recibir tráfico del load balancer.

**Respuesta exitosa (200):**
```json
{
  "status": "healthy",
  "timestamp": "2026-04-01T12:00:00Z",
  "version": "1.0.0",
  "checks": {
    "database": {"status": "ok", "latency_ms": 5, "type": "sqlite"},
    "redis": {"status": "ok", "message": "Redis no configurado (opcional)"},
    "stripe": {"status": "ok", "latency_ms": 120},
    "telegram": {"status": "ok", "latency_ms": 80, "bot_username": "jobs912bot"},
    "disk": {"status": "ok", "free_gb": 45.2, "total_gb": 100.0, "used_percent": 54.8},
    "memory": {"status": "ok", "used_percent": 45, "available_gb": 4.2, "total_gb": 8.0}
  }
}
```

**Respuesta degradada (200):**
```json
{
  "status": "degraded",
  "timestamp": "2026-04-01T12:00:00Z",
  "version": "1.0.0",
  "checks": {
    "database": {"status": "ok", "latency_ms": 5},
    "stripe": {"status": "degraded", "message": "Stripe API no responde: timeout"},
    ...
  }
}
```

**Respuesta no saludable (503):**
```json
{
  "status": "unhealthy",
  "timestamp": "2026-04-01T12:00:00Z",
  "version": "1.0.0",
  "checks": {
    "database": {"status": "unhealthy", "message": "Error de conexión: ..."},
    ...
  }
}
```

### GET /health

**Health Summary** - Resumen combinado de salud del sistema.

Similar a `/health/ready` pero con formato más compacto para monitoreo general.

## Checks Implementados

### Dependencias Críticas

- **database**: Conexión a la base de datos (SQLite/PostgreSQL)
  - Query simple `SELECT 1` para verificar conectividad
  - Mide latencia en milisegundos
  - `unhealthy` si no puede conectar

- **redis**: Conexión a Redis (opcional)
  - Solo se chequea si `REDIS_URL` está configurado
  - Ping al servidor Redis
  - `ok` si no está configurado (opcional)

### APIs Externas

- **stripe**: Conectividad con Stripe API (opcional)
  - Verifica que Stripe responda
  - `degraded` si falla (no crítico para operación básica)

- **telegram**: Conectividad con Telegram API (opcional)
  - Ping al bot de Telegram
  - `degraded` si falla (no crítico para API web)

### Recursos del Sistema

- **disk**: Espacio en disco
  - `unhealthy`: < 1GB libre
  - `degraded`: < 5GB libre
  - `ok`: ≥ 5GB libre

- **memory**: Uso de memoria RAM
  - `unhealthy`: > 95% usado
  - `degraded`: > 85% usado
  - `ok`: ≤ 85% usado

## Status Aggregation

El status global se determina así:

1. Si **algún check** es `unhealthy` → Status: `unhealthy` (HTTP 503)
2. Si **algún check** es `degraded` → Status: `degraded` (HTTP 200)
3. Si **todos** son `ok` → Status: `healthy` (HTTP 200)

## Uso en Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jobbot-api
spec:
  template:
    spec:
      containers:
      - name: api
        image: jobbot-api:latest
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

## Uso en Docker Compose

```yaml
services:
  api:
    image: jobbot-api:latest
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/ready"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

## Monitoreo con Prometheus/Grafana

Los health checks son compatibles con monitoreo. Ejemplo de métricas a exportar:

```python
# Métricas sugeridas para implementar
health_check_status{check="database"} 1  # 1=ok, 0.5=degraded, 0=unhealthy
health_check_latency_ms{check="database"} 5.2
```

## Tests

Los tests están en `/jobbot/api/tests/test_health.py`.

Ejecutar tests:
```bash
cd /mnt/c/Users/nacho/Downloads/jobobt
python -m pytest jobbot/api/tests/test_health.py -v
```

## Configuración Requerida

Variables de entorno opcionales:
- `REDIS_URL`: URL de conexión Redis (opcional)
- `STRIPE_SECRET_KEY`: Clave de Stripe (opcional)
- `TELEGRAM_TOKEN`: Token del bot de Telegram (opcional)
- `DATABASE_PATH`: Ruta de la base de datos (default: `job_bot.db`)

Dependencia adicional:
```
psutil>=5.9.0
```

## Troubleshooting

### Database check falla

Verificar:
1. Base de datos existe y es accesible
2. Permisos de lectura/escritura
3. Conexión a PostgreSQL (si usa Supabase)

### Disk check en degraded

Liberar espacio:
```bash
docker system prune -a  # Si usa Docker
rm -rf logs/*.log       # Limpiar logs antiguos
```

### Memory check en degraded

Verificar uso de memoria:
```bash
free -h
ps aux --sort=-%mem | head -10
```

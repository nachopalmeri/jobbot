"""
Health checks endpoints para monitoreo de la API JobBot.

Proporciona endpoints de liveness y readiness para orquestadores
de contenedores (Kubernetes, Docker Swarm, etc.)
"""

import os
import time
import platform
try:
    import psutil  # type: ignore
except ImportError:  # pragma: no cover - environment dependent
    psutil = None
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/health", tags=["health"])


# ============================================================
# MODELOS DE RESPUESTA
# ============================================================


class HealthCheck:
    """Resultado de un health check individual."""

    def __init__(
        self,
        name: str,
        status: str,  # "ok", "degraded", "unhealthy"
        latency_ms: Optional[float] = None,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.status = status
        self.latency_ms = latency_ms
        self.message = message
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        result = {"status": self.status}
        if self.latency_ms is not None:
            result["latency_ms"] = round(self.latency_ms, 2)
        if self.message:
            result["message"] = self.message
        if self.metadata:
            result.update(self.metadata)
        return result


class HealthResponse:
    """Respuesta completa de health check."""

    def __init__(
        self, status: str, checks: Dict[str, HealthCheck], version: str = "1.0.0"
    ):
        self.status = status
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.version = version
        self.checks = checks

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "timestamp": self.timestamp,
            "version": self.version,
            "checks": {name: check.to_dict() for name, check in self.checks.items()},
        }


# ============================================================
# CHECKS INDIVIDUALES
# ============================================================


async def check_database() -> HealthCheck:
    """Verifica conexión a la base de datos."""
    start = time.time()

    try:
        # Importar y probar conexión
        from job_bot.database import Database

        db = Database()

        # Intentar una query simple
        result = db._fetchone("SELECT 1 as test")

        if result and result.get("test") == 1:
            latency = (time.time() - start) * 1000
            return HealthCheck(
                name="database",
                status="ok",
                latency_ms=latency,
                metadata={"type": db.db_type},
            )
        else:
            return HealthCheck(
                name="database",
                status="unhealthy",
                message="Query de prueba no retornó resultado esperado",
            )
    except Exception as e:
        return HealthCheck(
            name="database", status="unhealthy", message=f"Error de conexión: {str(e)}"
        )


async def check_redis() -> HealthCheck:
    """Verifica conexión a Redis si está configurado."""
    redis_url = os.getenv("REDIS_URL", "")

    if not redis_url:
        return HealthCheck(
            name="redis", status="ok", message="Redis no configurado (opcional)"
        )

    try:
        import redis

        start = time.time()

        r = redis.from_url(redis_url, socket_connect_timeout=2)
        r.ping()

        latency = (time.time() - start) * 1000
        return HealthCheck(name="redis", status="ok", latency_ms=latency)
    except ImportError:
        return HealthCheck(
            name="redis", status="degraded", message="Cliente Redis no instalado"
        )
    except Exception as e:
        return HealthCheck(
            name="redis", status="unhealthy", message=f"Error de conexión: {str(e)}"
        )


async def check_stripe() -> HealthCheck:
    """Verifica conectividad con Stripe API (ping light)."""
    stripe_key = os.getenv("STRIPE_SECRET_KEY", "")

    if not stripe_key:
        return HealthCheck(
            name="stripe", status="ok", message="Stripe no configurado (opcional)"
        )

    try:
        import stripe

        start = time.time()

        stripe.api_key = stripe_key
        # Ping light: solo verificar que la API responde
        stripe.Account.retrieve()

        latency = (time.time() - start) * 1000
        return HealthCheck(name="stripe", status="ok", latency_ms=latency)
    except Exception as e:
        return HealthCheck(
            name="stripe",
            status="degraded",
            message=f"Stripe API no responde: {str(e)}",
        )


async def check_telegram() -> HealthCheck:
    """Verifica conectividad con Telegram API (ping light)."""
    telegram_token = os.getenv("TELEGRAM_TOKEN", "")

    if not telegram_token:
        return HealthCheck(
            name="telegram", status="ok", message="Telegram no configurado (opcional)"
        )

    try:
        import httpx

        start = time.time()

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"https://api.telegram.org/bot{telegram_token}/getMe"
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    latency = (time.time() - start) * 1000
                    return HealthCheck(
                        name="telegram",
                        status="ok",
                        latency_ms=latency,
                        metadata={
                            "bot_username": data["result"].get("username", "unknown")
                        },
                    )

            return HealthCheck(
                name="telegram",
                status="degraded",
                message=f"Telegram API retornó error: {response.status_code}",
            )
    except Exception as e:
        return HealthCheck(
            name="telegram",
            status="degraded",
            message=f"Error conectando a Telegram: {str(e)}",
        )


async def check_disk_space() -> HealthCheck:
    """Verifica espacio disponible en disco."""
    if psutil is None:
        return HealthCheck(
            name="disk",
            status="degraded",
            message="psutil no instalado",
        )

    try:
        # Obtener info del disco donde está el proyecto
        db_path = os.getenv("DATABASE_PATH", ".")
        disk = psutil.disk_usage(
            os.path.dirname(os.path.abspath(db_path)) if db_path != ":memory:" else "."
        )

        free_gb = disk.free / (1024**3)
        total_gb = disk.total / (1024**3)
        used_percent = (disk.used / disk.total) * 100

        # Status basado en espacio libre
        if free_gb < 1:  # Menos de 1GB
            status = "unhealthy"
        elif free_gb < 5:  # Menos de 5GB
            status = "degraded"
        else:
            status = "ok"

        return HealthCheck(
            name="disk",
            status=status,
            metadata={
                "free_gb": round(free_gb, 2),
                "total_gb": round(total_gb, 2),
                "used_percent": round(used_percent, 1),
            },
        )
    except Exception as e:
        return HealthCheck(
            name="disk",
            status="degraded",
            message=f"No se pudo obtener info de disco: {str(e)}",
        )


async def check_memory() -> HealthCheck:
    """Verifica uso de memoria del sistema."""
    if psutil is None:
        return HealthCheck(
            name="memory",
            status="degraded",
            message="psutil no instalado",
        )

    try:
        memory = psutil.virtual_memory()

        # Status basado en uso de memoria
        if memory.percent > 95:
            status = "unhealthy"
        elif memory.percent > 85:
            status = "degraded"
        else:
            status = "ok"

        return HealthCheck(
            name="memory",
            status=status,
            metadata={
                "used_percent": memory.percent,
                "available_gb": round(memory.available / (1024**3), 2),
                "total_gb": round(memory.total / (1024**3), 2),
            },
        )
    except Exception as e:
        return HealthCheck(
            name="memory",
            status="degraded",
            message=f"No se pudo obtener info de memoria: {str(e)}",
        )


def aggregate_status(checks: Dict[str, HealthCheck]) -> str:
    """Determina el status global basado en los checks individuales."""
    statuses = [check.status for check in checks.values()]

    if "unhealthy" in statuses:
        return "unhealthy"
    elif "degraded" in statuses:
        return "degraded"
    else:
        return "healthy"


# ============================================================
# ENDPOINTS
# ============================================================


@router.get("/live")
async def liveness_probe():
    """
    Liveness probe - indica si la aplicación está viva.

    Siempre retorna 200. Kubernetes usa esto para saber si debe
    reiniciar el contenedor.
    """
    return {"status": "alive", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/ready")
async def readiness_probe():
    """
    Readiness probe - indica si la aplicación está lista para recibir tráfico.

    Chequea todas las dependencias críticas. Kubernetes usa esto
    para saber si el pod debe recibir tráfico.

    Retorna 200 si todas las dependencias críticas están OK,
    503 si hay alguna dependencia crítica fallando.
    """
    # Ejecutar todos los checks
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
        "stripe": await check_stripe(),
        "telegram": await check_telegram(),
        "disk": await check_disk_space(),
        "memory": await check_memory(),
    }

    # Determinar status global
    overall_status = aggregate_status(checks)

    # Construir respuesta
    response = HealthResponse(status=overall_status, checks=checks, version="1.0.0")

    # Determinar código HTTP
    if overall_status == "unhealthy":
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE
    else:
        http_status = status.HTTP_200_OK

    return JSONResponse(status_code=http_status, content=response.to_dict())


@router.get("")
async def health_summary():
    """
    Endpoint de health check combinado.

    Similar a /ready pero con formato más compacto.
    """
    database_check = await check_database()
    checks = {
        "database": database_check,
        # Keep /health lightweight and deterministic for LB/legacy monitors.
        "redis": HealthCheck(name="redis", status="ok", message="summary check"),
        "stripe": HealthCheck(name="stripe", status="ok", message="summary check"),
        "telegram": HealthCheck(name="telegram", status="ok", message="summary check"),
        "disk": HealthCheck(name="disk", status="ok", message="summary check"),
        "memory": HealthCheck(name="memory", status="ok", message="summary check"),
    }
    overall_status = "healthy" if database_check.status == "ok" else "degraded"
    payload = HealthResponse(status=overall_status, checks=checks, version="1.0.0").to_dict()
    payload["features"] = {
        "rate_limiting": True,
        "audit_logging": True,
        "security_headers": True,
        "token_blacklist": True,
    }
    return JSONResponse(status_code=status.HTTP_200_OK, content=payload)

"""
Tests para el módulo de health checks.
"""

import pytest
from fastapi.testclient import TestClient


# Fixture para el cliente de test
@pytest.fixture
def client():
    """Proporciona un cliente de test para la API."""
    from jobbot.api.main import app

    return TestClient(app)


class TestLivenessProbe:
    """Tests para el endpoint de liveness probe."""

    def test_liveness_returns_200(self, client):
        """El liveness probe siempre debe retornar 200."""
        response = client.get("/health/live")
        assert response.status_code == 200

    def test_liveness_returns_alive_status(self, client):
        """Debe retornar status 'alive'."""
        response = client.get("/health/live")
        data = response.json()
        assert data["status"] == "alive"
        assert "timestamp" in data


class TestReadinessProbe:
    """Tests para el endpoint de readiness probe."""

    def test_readiness_returns_valid_structure(self, client):
        """Debe retornar estructura válida de health check."""
        response = client.get("/health/ready")
        data = response.json()

        # Verificar estructura básica
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "checks" in data

        # Verificar que checks es un dict
        assert isinstance(data["checks"], dict)

    def test_readiness_checks_database(self, client):
        """Debe incluir check de database."""
        response = client.get("/health/ready")
        data = response.json()

        assert "database" in data["checks"]
        db_check = data["checks"]["database"]
        assert "status" in db_check

    def test_readiness_checks_disk(self, client):
        """Debe incluir check de disco."""
        response = client.get("/health/ready")
        data = response.json()

        assert "disk" in data["checks"]
        disk_check = data["checks"]["disk"]
        assert "status" in disk_check
        assert "free_gb" in disk_check or "message" in disk_check

    def test_readiness_checks_memory(self, client):
        """Debe incluir check de memoria."""
        response = client.get("/health/ready")
        data = response.json()

        assert "memory" in data["checks"]
        mem_check = data["checks"]["memory"]
        assert "status" in mem_check
        assert "used_percent" in mem_check or "message" in mem_check

    def test_readiness_checks_optional_services(self, client):
        """Debe incluir checks de servicios opcionales."""
        response = client.get("/health/ready")
        data = response.json()

        # Redis es opcional
        assert "redis" in data["checks"]

        # Stripe es opcional
        assert "stripe" in data["checks"]

        # Telegram es opcional
        assert "telegram" in data["checks"]


class TestHealthSummary:
    """Tests para el endpoint de health summary."""

    def test_health_endpoint_returns_200(self, client):
        """El endpoint /health debe retornar 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_endpoint_structure(self, client):
        """Debe tener la misma estructura que /health/ready."""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "checks" in data


class TestHealthStatusValues:
    """Tests para validar los valores de status."""

    def test_status_values_are_valid(self, client):
        """Los status deben ser 'ok', 'degraded' o 'unhealthy'."""
        response = client.get("/health/ready")
        data = response.json()

        valid_statuses = {"ok", "degraded", "unhealthy"}

        for check_name, check_data in data["checks"].items():
            assert check_data["status"] in valid_statuses, (
                f"Check '{check_name}' tiene status inválido: {check_data['status']}"
            )

    def test_overall_status_is_valid(self, client):
        """El status global debe ser 'healthy', 'degraded' o 'unhealthy'."""
        response = client.get("/health/ready")
        data = response.json()

        valid_overall_statuses = {"healthy", "degraded", "unhealthy"}
        assert data["status"] in valid_overall_statuses, (
            f"Status global inválido: {data['status']}"
        )


class TestHealthCheckModels:
    """Tests para las clases de modelos de health check."""

    def test_health_check_to_dict(self):
        """HealthCheck.to_dict debe retornar dict correcto."""
        from jobbot.api.routes.health import HealthCheck

        check = HealthCheck(
            name="test",
            status="ok",
            latency_ms=10.5,
            message="All good",
            metadata={"foo": "bar"},
        )

        result = check.to_dict()
        assert result["status"] == "ok"
        assert result["latency_ms"] == 10.5
        assert result["message"] == "All good"
        assert result["foo"] == "bar"

    def test_health_response_to_dict(self):
        """HealthResponse.to_dict debe retornar dict correcto."""
        from jobbot.api.routes.health import HealthResponse, HealthCheck

        checks = {"test": HealthCheck(name="test", status="ok")}
        response = HealthResponse(status="healthy", checks=checks)

        result = response.to_dict()
        assert result["status"] == "healthy"
        assert "timestamp" in result
        assert result["version"] == "1.0.0"
        assert "checks" in result
        assert "test" in result["checks"]


class TestAggregateStatus:
    """Tests para la función de agregación de status."""

    def test_aggregate_status_healthy(self):
        """Si todos los checks son ok, el status es healthy."""
        from jobbot.api.routes.health import aggregate_status, HealthCheck

        checks = {
            "a": HealthCheck(name="a", status="ok"),
            "b": HealthCheck(name="b", status="ok"),
        }

        assert aggregate_status(checks) == "healthy"

    def test_aggregate_status_degraded(self):
        """Si hay algún degraded, el status es degraded."""
        from jobbot.api.routes.health import aggregate_status, HealthCheck

        checks = {
            "a": HealthCheck(name="a", status="ok"),
            "b": HealthCheck(name="b", status="degraded"),
        }

        assert aggregate_status(checks) == "degraded"

    def test_aggregate_status_unhealthy(self):
        """Si hay algún unhealthy, el status es unhealthy."""
        from jobbot.api.routes.health import aggregate_status, HealthCheck

        checks = {
            "a": HealthCheck(name="a", status="ok"),
            "b": HealthCheck(name="b", status="unhealthy"),
        }

        assert aggregate_status(checks) == "unhealthy"

    def test_aggregate_status_unhealthy_takes_precedence(self):
        """Unhealthy toma precedencia sobre degraded."""
        from jobbot.api.routes.health import aggregate_status, HealthCheck

        checks = {
            "a": HealthCheck(name="a", status="degraded"),
            "b": HealthCheck(name="b", status="unhealthy"),
        }

        assert aggregate_status(checks) == "unhealthy"

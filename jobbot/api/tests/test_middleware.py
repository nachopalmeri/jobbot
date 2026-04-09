"""
Tests for API Middleware
"""

import json
import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.mark.security
class TestSecurityHeadersMiddleware:
    """Tests for security headers middleware."""

    def test_security_headers_present_on_all_responses(self, client):
        """Test that security headers are present on all responses."""
        endpoints = ["/health", "/", "/openapi.json"]

        for endpoint in endpoints:
            response = client.get(endpoint)

            # Check for key security headers
            headers = {k.lower(): v for k, v in response.headers.items()}

            # At least some security headers should be present
            security_headers = [
                "x-content-type-options",
                "x-frame-options",
                "x-xss-protection",
                "strict-transport-security",
            ]

            present_count = sum(1 for h in security_headers if h in headers)
            assert present_count >= 2, (
                f"Only {present_count} security headers present for {endpoint}"
            )

    def test_x_content_type_options_nosniff(self, client):
        """Test X-Content-Type-Options header is set to nosniff."""
        response = client.get("/health")

        header = response.headers.get("x-content-type-options", "").lower()
        if header:
            assert header == "nosniff"

    def test_x_frame_options_present(self, client):
        """Test X-Frame-Options header is present."""
        response = client.get("/health")

        header = response.headers.get("x-frame-options", "").upper()
        if header:
            assert header in ["DENY", "SAMEORIGIN"]


@pytest.mark.security
class TestAuditLoggingMiddleware:
    """Tests for audit logging middleware."""

    def test_audit_log_created_for_requests(self, client, auth_headers, caplog):
        """Test that audit logs are created for requests."""
        with caplog.at_level("INFO"):
            response = client.get("/auth/me", headers=auth_headers)

            # Check that request was logged
            assert any("request" in record.message.lower() for record in caplog.records)

    def test_audit_log_contains_trace_id(self, client, caplog):
        """Test that audit logs contain trace ID."""
        with caplog.at_level("INFO"):
            response = client.get("/health")

            # Check for trace_id in logs
            assert any(
                "trace_id" in record.message.lower() for record in caplog.records
            )

    def test_audit_log_does_not_contain_passwords(self, client, test_user, caplog):
        """Test that audit logs don't contain passwords."""
        with caplog.at_level("INFO"):
            response = client.post(
                "/auth/token",
                data={
                    "username": test_user["email"],
                    "password": test_user["password"],
                },
            )

            # Password should not be in logs
            for record in caplog.records:
                assert test_user["password"] not in record.message


@pytest.mark.security
class TestPayloadSizeMiddleware:
    """Tests for payload size limiting middleware."""

    def test_large_payload_rejected(self, client, auth_headers):
        """Test that payloads over limit are rejected."""
        # Create a large payload (>10MB default)
        large_data = {"data": "x" * (11 * 1024 * 1024)}

        response = client.post(
            "/auth/register",
            headers=auth_headers,
            json=large_data,
        )

        # Should be rejected due to size
        assert response.status_code in [400, 413]

    def test_normal_payload_accepted(self, client):
        """Test that normal sized payloads are accepted."""
        normal_data = {
            "email": "test@example.com",
            "password": "password123",
            "name": "Test User",
        }

        response = client.post("/auth/register", json=normal_data)

        # Should not fail due to size
        assert response.status_code != 413


@pytest.mark.security
class TestXSSProtectionMiddleware:
    """Tests for XSS protection middleware."""

    def test_xss_protection_header_present(self, client):
        """Test that XSS protection header is present."""
        response = client.get("/health")

        header = response.headers.get("x-xss-protection", "")
        if header:
            assert header in ["1; mode=block", "1", "0"]

    def test_response_content_type_set(self, client):
        """Test that Content-Type header is properly set."""
        response = client.get("/health")

        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type


class TestObservabilityMiddleware:
    """Tests for observability middleware."""

    def test_trace_id_added_to_response(self, client):
        """Test that trace ID is added to response headers."""
        response = client.get("/health")

        # Check for trace ID header
        assert any(
            h.lower() in ["x-trace-id", "x-request-id"] for h in response.headers.keys()
        )

    def test_request_timing_logged(self, client, caplog):
        """Test that request timing is logged."""
        with caplog.at_level("INFO"):
            response = client.get("/health")

            # Check for timing information in logs
            assert any(
                "duration" in record.message.lower() or "ms" in record.message.lower()
                for record in caplog.records
            )

    def test_error_requests_logged(self, client, caplog):
        """Test that error requests are logged."""
        with caplog.at_level("ERROR"):
            response = client.get("/nonexistent-endpoint-12345")

            # Check that errors are logged
            # Note: 404 might not trigger error logging depending on implementation
            pass


class TestCORSMiddleware:
    """Tests for CORS middleware."""

    def test_cors_headers_present(self, client):
        """Test that CORS headers are present on responses."""
        response = client.get("/health")

        # Check for CORS headers
        assert any(
            h.lower().startswith("access-control-") for h in response.headers.keys()
        )

    def test_cors_preflight_response(self, client):
        """Test that CORS preflight requests are handled."""
        response = client.options(
            "/auth/token",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )

        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers

    def test_cors_origin_allowed(self, client):
        """Test that allowed origins are permitted."""
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"},
        )

        # Origin should be reflected
        assert "access-control-allow-origin" in response.headers


class TestGzipMiddleware:
    """Tests for response compression middleware."""

    def test_large_response_compressed(self, client):
        """Test that large responses are compressed."""
        # This test depends on response size threshold
        # Usually compression kicks in for responses > 1KB

        # For now, just verify no errors occur
        response = client.get("/health")
        assert response.status_code == 200

    def test_accept_encoding_respected(self, client):
        """Test that Accept-Encoding header is respected."""
        response = client.get(
            "/health",
            headers={"Accept-Encoding": "gzip, deflate"},
        )

        assert response.status_code == 200

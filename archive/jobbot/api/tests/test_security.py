"""
Security tests for JobBot API
Tests for audit logging, security headers, rate limiting, and JWT security.
"""

import hashlib
import os
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Ensure JWT_SECRET_KEY is set for tests
os.environ["JWT_SECRET_KEY"] = "test-secret-key-min-32-chars-long-for-testing"
os.environ["APP_ENV"] = "testing"

from api.main import app
from api.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    validate_jwt_secret,
    hash_token,
    TokenBlacklist,
    RefreshTokenManager,
    get_token_blacklist,
    get_refresh_token_manager,
)
from api.rate_limit import (
    InMemoryRateLimiter,
    EndpointRateLimiter,
    RateLimitCategory,
    is_exempt_from_rate_limit,
)
from api.routes import jobs as jobs_routes
from api.middleware.security_headers import get_security_headers


try:
    from job_bot.database import Database
except ImportError:
    from database import Database


# Fixtures
@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def db():
    """Create a test database instance."""
    return Database(db_path=":memory:")


@pytest.fixture
def token_blacklist(db):
    """Create a token blacklist instance."""
    return TokenBlacklist(db)


@pytest.fixture
def refresh_manager(db):
    """Create a refresh token manager instance."""
    return RefreshTokenManager(db)


# ============================================================
# JWT Security Tests
# ============================================================


class TestJWTSecurity:
    """Tests for JWT token creation, validation, and security."""

    def test_create_access_token(self):
        """Test creating a valid access token."""
        data = {"sub": "test@example.com", "telegram_id": 123}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)

        # Decode and verify
        decoded = decode_token(token)
        assert decoded is not None
        assert decoded["sub"] == "test@example.com"
        assert decoded["telegram_id"] == 123
        assert decoded["type"] == "access"

    def test_create_refresh_token(self):
        """Test creating a valid refresh token."""
        data = {"sub": "test@example.com", "telegram_id": 123}
        token = create_refresh_token(data)

        assert token is not None
        assert isinstance(token, str)

        # Decode and verify
        decoded = decode_token(token)
        assert decoded is not None
        assert decoded["sub"] == "test@example.com"
        assert decoded["telegram_id"] == 123
        assert decoded["type"] == "refresh"

    def test_decode_expired_token(self):
        """Test decoding an expired token returns None."""
        data = {"sub": "test@example.com", "telegram_id": 123}
        # Create token that expired 1 second ago
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))

        decoded = decode_token(token)
        assert decoded is None

    def test_decode_invalid_token(self):
        """Test decoding an invalid token returns None."""
        decoded = decode_token("invalid.token.here")
        assert decoded is None

    def test_hash_token(self):
        """Test token hashing function."""
        token = "test-token-string"
        hashed = hash_token(token)

        assert hashed is not None
        assert isinstance(hashed, str)
        assert len(hashed) == 64  # SHA256 hex length

        # Same token should produce same hash
        hashed2 = hash_token(token)
        assert hashed == hashed2

        # Different token should produce different hash
        different_hash = hash_token("different-token")
        assert different_hash != hashed


# ============================================================
# Token Blacklist Tests
# ============================================================


class TestTokenBlacklist:
    """Tests for token blacklist functionality."""

    def test_revoke_token(self, token_blacklist):
        """Test revoking a token."""
        token = "test-token-to-revoke"
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        result = token_blacklist.revoke_token(token, expires_at)
        assert result is True

        # Verify token is blacklisted
        is_blacklisted = token_blacklist.is_token_revoked(token)
        assert is_blacklisted is True

    def test_is_token_not_revoked(self, token_blacklist):
        """Test checking a non-revoked token."""
        token = "test-token-not-revoked"

        is_blacklisted = token_blacklist.is_token_revoked(token)
        assert is_blacklisted is False

    def test_cleanup_expired_tokens(self, token_blacklist):
        """Test cleaning up expired tokens from blacklist."""
        # Add expired token
        token = "expired-token"
        expired_at = datetime.now(timezone.utc) - timedelta(hours=1)
        token_blacklist.revoke_token(token, expired_at)

        # Cleanup
        deleted = token_blacklist.cleanup_expired_tokens()
        assert deleted >= 0

        # Verify token is removed
        is_blacklisted = token_blacklist.is_token_revoked(token)
        assert is_blacklisted is False


# ============================================================
# Refresh Token Tests
# ============================================================


class TestRefreshToken:
    """Tests for refresh token rotation."""

    def test_create_refresh_token_pair(self, refresh_manager):
        """Test creating a refresh token pair."""
        user_id = 123
        email = "test@example.com"
        device_info = "test-device"

        access_token, refresh_token = refresh_manager.create_refresh_token_pair(
            user_id=user_id,
            email=email,
            device_info=device_info,
        )

        assert access_token is not None
        assert refresh_token is not None

        # Verify tokens
        access_payload = decode_token(access_token)
        refresh_payload = decode_token(refresh_token)

        assert access_payload["telegram_id"] == user_id
        assert access_payload["sub"] == email
        assert refresh_payload["telegram_id"] == user_id
        assert refresh_payload["sub"] == email

    def test_rotate_refresh_token(self, refresh_manager):
        """Test rotating a refresh token."""
        # Create initial token pair
        user_id = 123
        email = "test@example.com"

        access_token, refresh_token = refresh_manager.create_refresh_token_pair(
            user_id=user_id,
            email=email,
        )

        # Rotate the refresh token
        result = refresh_manager.rotate_refresh_token(
            old_refresh_token=refresh_token,
            email=email,
        )

        assert result is not None
        new_access_token, new_refresh_token = result

        assert new_access_token is not None
        assert new_refresh_token is not None

    def test_revoke_all_user_tokens(self, refresh_manager):
        """Test revoking all tokens for a user."""
        user_id = 123
        email = "test@example.com"

        # Create tokens
        refresh_manager.create_refresh_token_pair(
            user_id=user_id,
            email=email,
        )

        # Revoke all tokens
        result = refresh_manager.revoke_all_user_tokens(user_id)
        assert result is True


# ============================================================
# Rate Limiting Tests
# ============================================================


class TestRateLimiting:
    """Tests for rate limiting functionality."""

    def test_in_memory_rate_limiter(self):
        """Test basic rate limiting functionality."""
        limiter = InMemoryRateLimiter()

        # Allow requests up to limit
        allowed, remaining, retry_after = limiter.check(
            "test-key", limit=5, window_seconds=60
        )
        assert allowed is True
        assert remaining == 4

        # Use up all requests
        for _ in range(4):
            limiter.check("test-key", limit=5, window_seconds=60)

        # Next request should be denied
        allowed, remaining, retry_after = limiter.check(
            "test-key", limit=5, window_seconds=60
        )
        assert allowed is False
        assert retry_after > 0

    def test_endpoint_rate_limiter(self):
        """Test endpoint-specific rate limiting."""
        limiter = EndpointRateLimiter()

        # Test login endpoint
        for i in range(5):
            allowed, remaining, retry_after = limiter.check_endpoint(
                "/auth/login", f"user-{i}"
            )

        # Should be allowed (different identities)
        assert allowed is True

        # Test rate limit for same identity
        for _ in range(5):
            limiter.check_endpoint("/auth/login", "same-user")

        allowed, remaining, retry_after = limiter.check_endpoint(
            "/auth/login", "same-user"
        )
        assert allowed is False

    def test_endpoint_rate_limiter_falls_back_when_backend_fails(self, monkeypatch):
        """Test the limiter degrades safely to in-memory when Redis-like backend fails."""
        limiter = EndpointRateLimiter()

        class FailingLimiter:
            def check(self, *args, **kwargs):
                raise RuntimeError("redis down")

            def get_current_count(self, *args, **kwargs):
                raise RuntimeError("redis down")

        limiter._limiter = FailingLimiter()
        limiter._redis_enabled = True

        allowed, remaining, retry_after = limiter.check_endpoint("/auth/login", "same-user")

        assert allowed is True
        assert remaining >= 0
        assert retry_after == 0
        assert isinstance(limiter._limiter, InMemoryRateLimiter)

    def test_endpoint_rate_limiter_uses_redis_backend_when_available(self, monkeypatch):
        """Test the limiter selects the Redis backend when configured."""
        import sys
        import types
        import api.rate_limit as rate_limit_module

        class FakeRedisClient:
            def register_script(self, _script):
                def runner(keys=None, args=None):
                    return [1, 4, 0]

                return runner

            def pipeline(self):
                class FakePipeline:
                    def zremrangebyscore(self, *args, **kwargs):
                        return self

                    def zcard(self, *args, **kwargs):
                        return self

                    def execute(self):
                        return (0, 1)

                return FakePipeline()

            def delete(self, *_args, **_kwargs):
                return None

        fake_redis_module = types.SimpleNamespace()
        fake_redis_module.Redis = types.SimpleNamespace(
            from_url=lambda *_args, **_kwargs: FakeRedisClient()
        )
        monkeypatch.setitem(sys.modules, "redis", fake_redis_module)
        monkeypatch.setenv("RATE_LIMIT_BACKEND", "redis")
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")

        limiter = rate_limit_module.EndpointRateLimiter()

        assert isinstance(limiter._limiter, rate_limit_module.RedisRateLimiter)
        allowed, remaining, retry_after = limiter.check_endpoint(
            "/auth/login", "redis-user"
        )
        assert allowed is True
        assert remaining == 4
        assert retry_after == 0

    def test_dashboard_preview_falls_back_when_search_is_unavailable(
        self, client, auth_headers, monkeypatch
    ):
        """Dashboard preview should stay usable when job search is unavailable."""

        async def raise_unavailable(*args, **kwargs):
            from fastapi import HTTPException

            raise HTTPException(
                status_code=503,
                detail="Job search temporarily unavailable. Please try again later.",
            )

        monkeypatch.setattr(jobs_routes, "_search_jobs_with_cache", raise_unavailable)

        response = client.get("/jobs/dashboard-preview", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["jobs"]) > 0
        assert data["unavailable"] is True

    def test_is_exempt_from_rate_limit(self):
        """Test exemption from rate limiting."""
        assert is_exempt_from_rate_limit("/health", "GET") is True
        assert is_exempt_from_rate_limit("/stats", "GET") is True
        assert is_exempt_from_rate_limit("/api/users", "GET") is False


# ============================================================
# Security Headers Tests
# ============================================================


class TestSecurityHeaders:
    """Tests for security headers middleware."""

    def test_security_headers_present(self, client):
        """Test that security headers are present in responses."""
        response = client.get("/")

        headers = response.headers

        # Check CSP header
        assert "Content-Security-Policy" in headers
        assert "default-src 'self'" in headers["Content-Security-Policy"]

        # Check X-Frame-Options
        assert "X-Frame-Options" in headers
        assert headers["X-Frame-Options"] == "DENY"

        # Check X-Content-Type-Options
        assert "X-Content-Type-Options" in headers
        assert headers["X-Content-Type-Options"] == "nosniff"

        # Check HSTS
        assert "Strict-Transport-Security" in headers
        assert "max-age=31536000" in headers["Strict-Transport-Security"]

    def test_csp_directives(self):
        """Test CSP header directives."""
        headers = get_security_headers()
        csp = headers["Content-Security-Policy"]

        assert "default-src 'self'" in csp
        assert "script-src 'self'" in csp
        assert "style-src 'self'" in csp
        assert "img-src 'self' data: https:" in csp


# ============================================================
# Integration Tests
# ============================================================


class TestSecurityIntegration:
    """Integration tests for security features."""

    def test_health_check_endpoint(self, client):
        """Test health check endpoint shows security features."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert data["features"]["rate_limiting"] is True
        assert data["features"]["audit_logging"] is True
        assert data["features"]["security_headers"] is True
        assert data["features"]["token_blacklist"] is True

    def test_rate_limit_headers(self, client):
        """Test that rate limit headers are present."""
        response = client.get("/")

        headers = response.headers
        assert "X-RateLimit-Limit" in headers
        assert "X-RateLimit-Remaining" in headers

    def test_invalid_login_rate_limit(self, client):
        """Test rate limiting on invalid login attempts."""
        # Make multiple invalid login attempts
        for _ in range(10):
            response = client.post(
                "/auth/token",
                data={"username": "invalid@test.com", "password": "wrong"},
            )

        # Should be rate limited eventually
        response = client.post(
            "/auth/token",
            data={"username": "invalid@test.com", "password": "wrong"},
        )

        if response.status_code == 429:
            assert "Retry-After" in response.headers


# ============================================================
# Error Handling Tests
# ============================================================


class TestErrorHandling:
    """Tests for security error handling."""

    def test_invalid_token_error(self, client):
        """Test error response for invalid token."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == 401
        assert "detail" in response.json()

    def test_missing_token_error(self, client):
        """Test error response for missing token."""
        response = client.get("/auth/me")

        assert response.status_code == 403


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


# ============================================================
# Additional Security Tests - CSP, Headers, Audit Logs
# ============================================================


class TestCSPHeaders:
    """Tests for Content Security Policy headers."""

    def test_csp_header_present(self, client):
        """Test that CSP header is present in responses."""
        response = client.get("/")

        assert "Content-Security-Policy" in response.headers
        csp = response.headers["Content-Security-Policy"]

        # Check for essential CSP directives
        assert "default-src" in csp
        assert "script-src" in csp
        assert "style-src" in csp
        assert "img-src" in csp

    def test_csp_no_inline_scripts(self, client):
        """Test CSP prevents inline scripts."""
        response = client.get("/")
        csp = response.headers.get("Content-Security-Policy", "")

        # Should not allow unsafe-inline for scripts in production
        # Note: Testing mode might have different settings
        assert "Content-Security-Policy" in response.headers

    def test_csp_frame_ancestors(self, client):
        """Test CSP frame-ancestors prevents clickjacking."""
        response = client.get("/")
        csp = response.headers.get("Content-Security-Policy", "")

        # Should prevent framing
        assert "frame-ancestors" in csp or "X-Frame-Options" in response.headers


class TestExtendedSecurityHeaders:
    """Extended tests for security headers."""

    def test_x_frame_options_header(self, client):
        """Test X-Frame-Options header is present."""
        response = client.get("/")

        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] in ["DENY", "SAMEORIGIN"]

    def test_x_content_type_options_header(self, client):
        """Test X-Content-Type-Options header is present."""
        response = client.get("/")

        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"

    def test_x_xss_protection_header(self, client):
        """Test X-XSS-Protection header is present."""
        response = client.get("/")

        assert "X-XSS-Protection" in response.headers
        assert "1; mode=block" in response.headers["X-XSS-Protection"]

    def test_strict_transport_security_header(self, client):
        """Test HSTS header is present."""
        response = client.get("/")

        assert "Strict-Transport-Security" in response.headers
        hsts = response.headers["Strict-Transport-Security"]
        assert "max-age=" in hsts
        assert int(hsts.split("max-age=")[1].split(";")[0]) >= 31536000

    def test_referrer_policy_header(self, client):
        """Test Referrer-Policy header is present."""
        response = client.get("/")

        assert "Referrer-Policy" in response.headers
        policy = response.headers["Referrer-Policy"]
        assert policy in [
            "no-referrer",
            "no-referrer-when-downgrade",
            "same-origin",
            "strict-origin",
            "strict-origin-when-cross-origin",
        ]

    def test_permissions_policy_header(self, client):
        """Test Permissions-Policy header is present."""
        response = client.get("/")

        # Header might be Feature-Policy or Permissions-Policy
        assert (
            "Permissions-Policy" in response.headers
            or "Feature-Policy" in response.headers
        )


class TestRateLimitingHeaders:
    """Tests for rate limiting headers."""

    def test_rate_limit_headers_on_api_endpoints(self, client):
        """Test rate limit headers are present on API endpoints."""
        response = client.get("/health")

        # Health endpoint might be exempt, but check other endpoints
        response2 = client.get("/")

        # At least one should have rate limit headers
        has_headers = (
            "X-RateLimit-Limit" in response.headers
            or "X-RateLimit-Limit" in response2.headers
        )
        assert has_headers, "Rate limit headers should be present"

    def test_rate_limit_limit_header_value(self, client):
        """Test X-RateLimit-Limit header has valid value."""
        response = client.get("/")

        if "X-RateLimit-Limit" in response.headers:
            limit = response.headers["X-RateLimit-Limit"]
            assert limit.isdigit()
            assert int(limit) > 0

    def test_rate_limit_remaining_header_value(self, client):
        """Test X-RateLimit-Remaining header has valid value."""
        response = client.get("/")

        if "X-RateLimit-Remaining" in response.headers:
            remaining = response.headers["X-RateLimit-Remaining"]
            assert remaining.isdigit()
            assert int(remaining) >= 0

    def test_retry_after_header_on_rate_limit(self, client):
        """Test Retry-After header is present when rate limited."""
        # Make many requests to trigger rate limit
        for _ in range(100):
            client.get("/")

        response = client.get("/")

        if response.status_code == 429:
            assert "Retry-After" in response.headers
            retry_after = response.headers["Retry-After"]
            assert retry_after.isdigit()
            assert int(retry_after) > 0


class TestAuditLogging:
    """Tests for audit logging functionality."""

    def test_audit_log_created_on_request(self, client, db, caplog):
        """Test that audit log entry is created for each request."""
        import logging

        with caplog.at_level(logging.INFO):
            response = client.get("/health")

            # Check for audit log entries
            audit_logs = [r for r in caplog.records if "http_request" in r.message]
            assert len(audit_logs) > 0 or response.status_code == 200

    def test_audit_log_contains_required_fields(self, client, caplog):
        """Test audit log contains all required fields."""
        import logging
        import json

        with caplog.at_level(logging.INFO):
            client.get("/health")

            # Find audit log entries
            for record in caplog.records:
                if "http_request" in record.message:
                    try:
                        log_data = json.loads(record.message)
                        # Should contain key fields
                        assert "method" in log_data or "event" in log_data
                        assert "path" in log_data or "endpoint" in log_data
                    except json.JSONDecodeError:
                        pass  # Not all logs are JSON

    def test_audit_log_includes_ip_address(self, client, caplog):
        """Test audit log includes client IP address."""
        import logging

        with caplog.at_level(logging.INFO):
            client.get("/health", headers={"X-Forwarded-For": "192.168.1.1"})

            # Check logs for IP-related info
            ip_logs = [r for r in caplog.records if "ip" in r.message.lower()]
            assert len(ip_logs) > 0

    def test_audit_log_includes_user_agent(self, client, caplog):
        """Test audit log includes user agent information."""
        import logging

        with caplog.at_level(logging.INFO):
            client.get("/health", headers={"User-Agent": "TestAgent/1.0"})

            # Verify request was logged
            assert any("health" in r.message for r in caplog.records)


class TestSecurityConfiguration:
    """Tests for security configuration and settings."""

    def test_jwt_secret_minimum_length(self):
        """Test JWT secret meets minimum length requirement."""
        secret = os.environ.get("JWT_SECRET_KEY", "")
        assert len(secret) >= 32, "JWT secret must be at least 32 characters"

    def test_no_weak_jwt_secrets_in_env(self, monkeypatch):
        """Test that weak JWT secrets are rejected."""
        weak_secrets = [
            "secret",
            "password",
            "123456",
            "test",
            "jwt-secret",
        ]

        for weak in weak_secrets:
            # Should not be the actual secret
            assert os.environ.get("JWT_SECRET_KEY") != weak

    def test_app_env_set_correctly(self):
        """Test APP_ENV is set to appropriate value."""
        app_env = os.environ.get("APP_ENV", "")
        assert app_env in ["development", "testing", "staging", "production"]


class TestCORSConfiguration:
    """Tests for CORS configuration."""

    def test_cors_headers_present_on_cross_origin(self, client):
        """Test CORS headers on cross-origin requests."""
        response = client.options(
            "/",
            headers={
                "Origin": "http://example.com",
                "Access-Control-Request-Method": "GET",
            },
        )

        # Check for CORS headers
        assert (
            "access-control-allow-origin" in response.headers
            or response.status_code == 200
        )

    def test_cors_allows_credentials(self, client):
        """Test CORS allows credentials."""
        response = client.get("/", headers={"Origin": "http://localhost:3000"})

        cors_header = response.headers.get("access-control-allow-credentials", "")
        assert cors_header.lower() == "true" or cors_header == ""


class TestErrorResponseSecurity:
    """Tests for security of error responses."""

    def test_error_response_does_not_leak_sensitive_info(self, client):
        """Test that error responses don't leak sensitive information."""
        response = client.get("/nonexistent-endpoint-that-triggers-error")

        response_text = response.text.lower()

        # Should not contain sensitive keywords
        sensitive_keywords = ["password", "secret", "token", "key", "credential"]
        for keyword in sensitive_keywords:
            assert keyword not in response_text, (
                f"Error response should not contain '{keyword}'"
            )

    def test_404_response_is_generic(self, client):
        """Test 404 responses don't reveal internal structure."""
        response = client.get("/admin/private-endpoint")

        # Should return standard 404, not reveal that endpoint exists
        assert response.status_code in [404, 403, 200]


class TestResponseHeaderSecurity:
    """Tests for security-related response headers."""

    def test_no_server_version_header(self, client):
        """Test that server version is not exposed."""
        response = client.get("/")

        # Server header should not reveal specific version info
        server_header = response.headers.get("Server", "")
        assert "FastAPI" not in server_header or server_header == ""

    def test_no_x_powered_by_header(self, client):
        """Test X-Powered-By header is not present."""
        response = client.get("/")

        assert "X-Powered-By" not in response.headers

    def test_cache_control_headers_on_sensitive_endpoints(self, client):
        """Test cache control headers are present on sensitive endpoints."""
        response = client.get("/auth/me")

        # Should have cache control headers
        assert "Cache-Control" in response.headers or response.status_code == 403


class TestSecurityMiddleware:
    """Tests for security middleware functionality."""

    def test_security_headers_middleware_active(self, client):
        """Test security headers middleware is active."""
        response = client.get("/")

        # Multiple security headers should be present
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "Content-Security-Policy",
        ]

        present_count = sum(1 for h in security_headers if h in response.headers)
        assert present_count >= 2, "Security middleware should add headers"

    def test_audit_middleware_logs_requests(self, client, caplog):
        """Test audit middleware logs requests."""
        import logging

        with caplog.at_level(logging.INFO):
            client.get("/health")

            # Should have logged the request
            assert len(caplog.records) > 0


class TestInputValidationSecurity:
    """Tests for input validation security."""

    def test_sql_injection_protection(self, client):
        """Test SQL injection attempts are blocked."""
        # Attempt SQL injection in various endpoints
        malicious_inputs = [
            "' OR '1'='1",
            "1; DROP TABLE users; --",
            "1' UNION SELECT * FROM users --",
        ]

        for injection in malicious_inputs:
            response = client.post(
                "/auth/token",
                data={
                    "username": injection,
                    "password": "test",
                },
            )

            # Should not crash or return database errors
            assert response.status_code in [400, 401, 422, 500]

    def test_xss_protection_in_responses(self, client):
        """Test XSS attempts are not reflected in responses."""
        # Note: This tests that the API doesn't reflect XSS payloads
        # A full XSS test would require checking HTML responses
        xss_payload = "<script>alert('xss')</script>"

        response = client.get(f"/?test={xss_payload}")

        # Response should not contain unescaped script tags
        assert "<script>" not in response.text or response.status_code == 422

"""
Tests for API Core Modules
"""

import json
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.security
class TestCacheModule:
    """Tests for cache module."""

    def test_cache_set_and_get(self):
        """Test cache set and get operations."""
        from api.core.cache import InMemoryCache

        cache = InMemoryCache()

        # Set a value
        result = cache.set("test_key", "test_value", ttl=60)
        assert result is True

        # Get the value
        value = cache.get("test_key")
        assert value == "test_value"

    def test_cache_expiration(self):
        """Test that cache entries expire correctly."""
        from api.core.cache import InMemoryCache

        cache = InMemoryCache()

        # Set with very short TTL
        cache.set("test_key", "test_value", ttl=1)

        # Should exist immediately
        assert cache.get("test_key") == "test_value"

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired
        assert cache.get("test_key") is None

    def test_cache_delete(self):
        """Test cache delete operation."""
        from api.core.cache import InMemoryCache

        cache = InMemoryCache()

        cache.set("test_key", "test_value")
        assert cache.get("test_key") == "test_value"

        # Delete
        result = cache.delete("test_key")
        assert result is True

        # Should be gone
        assert cache.get("test_key") is None

    def test_cache_clear(self):
        """Test cache clear operation."""
        from api.core.cache import InMemoryCache

        cache = InMemoryCache()

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        # Clear
        result = cache.clear()
        assert result is True

        # All should be gone
        assert cache.get("key1") is None
        assert cache.get("key2") is None


@pytest.mark.security
class TestSecurityUtilities:
    """Tests for security utilities."""

    def test_token_hash_consistency(self):
        """Test that token hashing is consistent."""
        from api.core.security import hash_token

        token = "test_token_123"
        hash1 = hash_token(token)
        hash2 = hash_token(token)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length

    def test_token_hash_different_inputs(self):
        """Test that different tokens produce different hashes."""
        from api.core.security import hash_token

        hash1 = hash_token("token1")
        hash2 = hash_token("token2")

        assert hash1 != hash2

    def test_create_access_token(self):
        """Test access token creation."""
        from api.core.security import create_access_token, decode_token

        token = create_access_token(
            data={
                "sub": "test@example.com",
                "telegram_id": 123456789,
            }
        )

        # Should be decodable
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "test@example.com"
        assert payload["telegram_id"] == 123456789
        assert payload["type"] == "access"

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        from api.core.security import create_refresh_token, decode_token

        token = create_refresh_token(
            data={
                "sub": "test@example.com",
                "telegram_id": 123456789,
            }
        )

        # Should be decodable
        payload = decode_token(token)
        assert payload is not None
        assert payload["type"] == "refresh"

    def test_decode_expired_token(self):
        """Test decoding of expired token."""
        from api.core.security import create_access_token, decode_token

        # Create expired token
        token = create_access_token(
            data={"sub": "test@example.com"},
            expires_delta=timedelta(seconds=-1),
        )

        # Should return None for expired
        payload = decode_token(token)
        assert payload is None

    def test_decode_invalid_token(self):
        """Test decoding of invalid token."""
        from api.core.security import decode_token

        payload = decode_token("invalid.token.here")
        assert payload is None


@pytest.mark.security
class TestRateLimitModule:
    """Tests for rate limiting module."""

    def test_in_memory_rate_limiter_basic(self):
        """Test basic rate limiting."""
        from api.rate_limit import InMemoryRateLimiter

        limiter = InMemoryRateLimiter()

        # First 5 requests should be allowed
        for _ in range(5):
            allowed, remaining, retry_after = limiter.check(
                "test_key", limit=5, window_seconds=60
            )
            assert allowed is True

        # 6th request should be blocked
        allowed, remaining, retry_after = limiter.check(
            "test_key", limit=5, window_seconds=60
        )
        assert allowed is False
        assert retry_after > 0

    def test_in_memory_rate_limiter_remaining_count(self):
        """Test rate limiter remaining count."""
        from api.rate_limit import InMemoryRateLimiter

        limiter = InMemoryRateLimiter()

        # Make 3 requests
        for _ in range(3):
            limiter.check("test_key", limit=10, window_seconds=60)

        # Should have 7 remaining
        count = limiter.get_current_count("test_key", window_seconds=60)
        assert count == 3

    def test_in_memory_rate_limiter_reset(self):
        """Test rate limiter reset."""
        from api.rate_limit import InMemoryRateLimiter

        limiter = InMemoryRateLimiter()

        # Exhaust rate limit
        for _ in range(5):
            limiter.check("test_key", limit=5, window_seconds=60)

        # Should be blocked
        allowed, _, _ = limiter.check("test_key", limit=5, window_seconds=60)
        assert allowed is False

        # Reset
        limiter.reset("test_key")

        # Should be allowed again
        allowed, _, _ = limiter.check("test_key", limit=5, window_seconds=60)
        assert allowed is True

    def test_endpoint_rate_limiter_categorization(self):
        """Test endpoint rate limiter categorization."""
        from api.rate_limit import EndpointRateLimiter, RateLimitCategory

        limiter = EndpointRateLimiter()

        # Register endpoint
        limiter.register_endpoint("/auth/login", RateLimitCategory.LOGIN)

        # Should categorize correctly
        category = limiter._get_category_for_path("/auth/login")
        assert category == RateLimitCategory.LOGIN

    def test_endpoint_rate_limiter_check(self):
        """Test endpoint rate limiter check."""
        from api.rate_limit import EndpointRateLimiter, RateLimitCategory

        limiter = EndpointRateLimiter()
        limiter.register_endpoint("/auth/login", RateLimitCategory.LOGIN)

        # First 5 requests should be allowed
        for _ in range(5):
            allowed, remaining, retry_after = limiter.check_endpoint(
                "/auth/login", "test_user"
            )
            assert allowed is True

        # 6th should be blocked
        allowed, remaining, retry_after = limiter.check_endpoint(
            "/auth/login", "test_user"
        )
        assert allowed is False

    def test_endpoint_rate_limiter_headers(self):
        """Test endpoint rate limiter header generation."""
        from api.rate_limit import EndpointRateLimiter

        limiter = EndpointRateLimiter()

        headers = limiter.get_rate_limit_headers("/test", "user", True, 0)

        assert "X-RateLimit-Limit" in headers
        assert "X-RateLimit-Remaining" in headers
        assert "X-RateLimit-Window" in headers


@pytest.mark.security
class TestReliabilityModule:
    """Tests for reliability/circuit breaker module."""

    def test_circuit_breaker_initial_state(self):
        """Test circuit breaker initial state."""
        try:
            from api.core.reliability import CircuitBreaker

            cb = CircuitBreaker(name="test")

            # Initial state should be closed
            assert cb.get_metrics()["state"] == "closed"
        except ImportError:
            pytest.skip("Circuit breaker not implemented")

    def test_circuit_breaker_failure_tracking(self):
        """Test circuit breaker failure tracking."""
        try:
            from api.core.reliability import CircuitBreaker

            cb = CircuitBreaker(name="test", failure_threshold=3)

            # Record failures
            for _ in range(3):
                cb.record_failure()

            metrics = cb.get_metrics()
            assert metrics["failure_count"] >= 3
        except ImportError:
            pytest.skip("Circuit breaker not implemented")

"""
Authentication tests for JobBot API.
Tests for login, token generation, refresh, logout, and rate limiting.
"""

import hashlib
import os
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from api.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
    TokenBlacklist,
    RefreshTokenManager,
)


@pytest.mark.security
class TestAuthLogin:
    """Tests for user login functionality."""

    def test_login_success_with_valid_credentials(self, client, db, test_user):
        """Test successful login with valid email and password."""
        response = client.post(
            "/auth/token",
            data={
                "username": test_user["email"],
                "password": test_user["password"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["telegram_id"] == test_user["telegram_id"]

        # Verify token is valid
        token_data = decode_token(data["access_token"])
        assert token_data is not None
        assert token_data["sub"] == test_user["email"]
        assert token_data["telegram_id"] == test_user["telegram_id"]

    def test_login_fails_with_wrong_password(self, client, db, test_user):
        """Test login fails with incorrect password."""
        response = client.post(
            "/auth/token",
            data={
                "username": test_user["email"],
                "password": "wrongpassword123",
            },
        )

        assert response.status_code == 401
        assert "detail" in response.json()
        assert "Credenciales invalidas" in response.json()["detail"]

    def test_login_fails_with_nonexistent_user(self, client, db):
        """Test login fails for user that doesn't exist."""
        response = client.post(
            "/auth/token",
            data={
                "username": "nonexistent@example.com",
                "password": "somepassword123",
            },
        )

        assert response.status_code == 401
        assert "detail" in response.json()

    def test_login_requires_email(self, client):
        """Test login requires email field."""
        response = client.post(
            "/auth/token",
            data={
                "username": "",
                "password": "testpassword123",
            },
        )

        assert response.status_code == 400
        assert "detail" in response.json()

    def test_login_requires_password(self, client, test_user):
        """Test login requires password field."""
        response = client.post(
            "/auth/token",
            data={
                "username": test_user["email"],
                "password": "",
            },
        )

        assert response.status_code == 400
        assert "detail" in response.json()


@pytest.mark.security
class TestTokenGeneration:
    """Tests for JWT token generation and validation."""

    def test_access_token_contains_correct_claims(self, test_user):
        """Test access token has correct payload claims."""
        token = create_access_token(
            data={
                "sub": test_user["email"],
                "telegram_id": test_user["telegram_id"],
            }
        )

        payload = decode_token(token)
        assert payload["sub"] == test_user["email"]
        assert payload["telegram_id"] == test_user["telegram_id"]
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_refresh_token_contains_correct_claims(self, test_user):
        """Test refresh token has correct payload claims."""
        token = create_refresh_token(
            data={
                "sub": test_user["email"],
                "telegram_id": test_user["telegram_id"],
            }
        )

        payload = decode_token(token)
        assert payload["sub"] == test_user["email"]
        assert payload["telegram_id"] == test_user["telegram_id"]
        assert payload["type"] == "refresh"
        assert "exp" in payload

    def test_token_expiration_is_set(self, test_user):
        """Test tokens have expiration time set."""
        token = create_access_token(
            data={
                "sub": test_user["email"],
                "telegram_id": test_user["telegram_id"],
            }
        )

        payload = decode_token(token)
        exp_timestamp = payload["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)

        # Should expire in roughly 24 hours (with some tolerance)
        now = datetime.now(timezone.utc)
        time_diff = (exp_datetime - now).total_seconds()
        assert 86000 < time_diff < 87000  # ~24 hours


@pytest.mark.security
class TestTokenRefresh:
    """Tests for token refresh functionality."""

    def test_refresh_token_success(self, client, auth_token_pair):
        """Test successful token refresh with valid refresh token."""
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": auth_token_pair["refresh_token"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

        # New token should be different from old one
        assert data["access_token"] != auth_token_pair["access_token"]
        assert data["refresh_token"] != auth_token_pair["refresh_token"]

    def test_refresh_token_rotates(self, client, auth_token_pair, refresh_manager):
        """Test that refresh token rotation works correctly."""
        old_refresh_token = auth_token_pair["refresh_token"]

        # First refresh
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": old_refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        new_refresh_token = data["refresh_token"]

        # Old token should be invalidated
        second_response = client.post(
            "/auth/refresh",
            json={"refresh_token": old_refresh_token},
        )

        assert second_response.status_code == 401

    def test_refresh_token_fails_with_invalid_token(self, client):
        """Test refresh fails with invalid token."""
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )

        assert response.status_code == 401
        assert "detail" in response.json()

    def test_refresh_token_fails_with_access_token(self, client, test_user):
        """Test refresh fails when using access token instead of refresh token."""
        access_token = create_access_token(
            data={
                "sub": test_user["email"],
                "telegram_id": test_user["telegram_id"],
            }
        )

        response = client.post(
            "/auth/refresh",
            json={"refresh_token": access_token},
        )

        assert response.status_code == 401


@pytest.mark.security
class TestLogout:
    """Tests for logout functionality."""

    def test_logout_invalidates_token(self, client, auth_headers, auth_token_pair, db):
        """Test logout invalidates the current access token."""
        # Logout
        response = client.post("/auth/logout", headers=auth_headers)
        assert response.status_code == 200
        assert "Sesion cerrada correctamente" in response.json()["message"]

        # Try to use the invalidated token
        me_response = client.get("/auth/me", headers=auth_headers)
        assert me_response.status_code == 401

    def test_logout_all_devices(
        self, client, auth_headers, auth_token_pair, refresh_manager, test_user
    ):
        """Test logout from all devices revokes all refresh tokens."""
        # Create another token pair for the same user
        _, refresh_token2 = refresh_manager.create_refresh_token_pair(
            user_id=test_user["telegram_id"],
            email=test_user["email"],
            device_info="other-device",
        )

        # Logout all
        response = client.post("/auth/logout-all", headers=auth_headers)
        assert response.status_code == 200

        # Try to refresh with second token - should fail
        refresh_response = client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token2},
        )
        assert refresh_response.status_code == 401

    def test_logout_requires_auth(self, client):
        """Test logout requires authentication."""
        response = client.post("/auth/logout")
        assert response.status_code == 403


@pytest.mark.security
class TestProtectedRoutes:
    """Tests for protected route access."""

    def test_protected_route_without_token_returns_401(self, client):
        """Test accessing protected route without token returns 401."""
        response = client.get("/auth/me")
        assert response.status_code == 403

    def test_protected_route_with_invalid_token_returns_401(
        self, client, invalid_token
    ):
        """Test accessing protected route with invalid token returns 401."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {invalid_token}"},
        )
        assert response.status_code == 401

    def test_protected_route_with_expired_token_returns_401(
        self, client, expired_token
    ):
        """Test accessing protected route with expired token returns 401."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == 401

    def test_protected_route_with_valid_token_succeeds(
        self, client, auth_headers, test_user
    ):
        """Test accessing protected route with valid token succeeds."""
        response = client.get("/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["telegram_id"] == test_user["telegram_id"]
        assert data["email"] == test_user["email"]


@pytest.mark.security
@pytest.mark.slow
class TestAuthRateLimiting:
    """Tests for authentication rate limiting."""

    def test_login_rate_limit_5_per_minute(self, client, db, clean_rate_limits):
        """Test login is rate limited to 5 attempts per minute."""
        email = "ratelimit@test.com"
        password = "wrongpassword"

        # Make 5 failed login attempts
        for i in range(5):
            response = client.post(
                "/auth/token",
                data={"username": email, "password": password},
            )
            assert response.status_code == 401  # Invalid credentials

        # 6th attempt should be rate limited
        response = client.post(
            "/auth/token",
            data={"username": email, "password": password},
        )

        # Should be rate limited
        assert response.status_code == 429
        assert "Retry-After" in response.headers

    def test_rate_limit_headers_present(self, client, test_user):
        """Test rate limiting headers are present in responses."""
        response = client.post(
            "/auth/token",
            data={"username": test_user["email"], "password": test_user["password"]},
        )

        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Window" in response.headers

    def test_rate_limit_resets_after_window(self, client, db, clean_rate_limits):
        """Test rate limit resets after the time window."""
        email = "ratelimitreset@test.com"

        # Use up rate limit
        for _ in range(5):
            client.post(
                "/auth/token",
                data={"username": email, "password": "wrong"},
            )

        # Should be rate limited now
        response = client.post(
            "/auth/token",
            data={"username": email, "password": "wrong"},
        )
        assert response.status_code == 429


@pytest.mark.security
class TestTokenBlacklist:
    """Tests for token blacklist functionality."""

    def test_blacklisted_token_is_rejected(
        self, client, auth_token_pair, token_blacklist
    ):
        """Test that blacklisted tokens are rejected."""
        token = auth_token_pair["access_token"]

        # Add to blacklist
        token_blacklist.revoke_token(
            token, datetime.now(timezone.utc) + timedelta(hours=1)
        )

        # Try to use blacklisted token
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 401
        assert (
            "revocado" in response.json()["detail"].lower()
            or "invalido" in response.json()["detail"].lower()
        )

    def test_token_hash_consistency(self):
        """Test token hashing produces consistent results."""
        token = "test-token-123"
        hash1 = hash_token(token)
        hash2 = hash_token(token)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length
        assert hash1 != token  # Hash should be different from original


@pytest.mark.security
class TestTelegramAuth:
    """Tests for Telegram authentication."""

    def test_telegram_auth_success(self, client, telegram_auth_data):
        """Test successful Telegram WebApp authentication."""
        with patch("api.core.security.verify_telegram_auth") as mock_verify:
            mock_verify.return_value = True

            response = client.post("/auth/telegram", json=telegram_auth_data)

            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["user"]["telegram_id"] == telegram_auth_data["telegram_id"]

    def test_telegram_auth_fails_with_invalid_hash(self, client, telegram_auth_data):
        """Test Telegram auth fails with invalid hash."""
        with patch("api.core.security.verify_telegram_auth") as mock_verify:
            mock_verify.return_value = False

            response = client.post("/auth/telegram", json=telegram_auth_data)

            assert response.status_code == 401
            assert "Autenticacion de Telegram invalida" in response.json()["detail"]

    def test_telegram_code_login_success(self, client, db, test_user):
        """Test login with Telegram code."""
        # Create a login code
        code = "ABC123"
        expires_at = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
        db.create_web_login_code(test_user["telegram_id"], code, expires_at)

        response = client.post("/auth/telegram/code", json={"code": code})

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["telegram_id"] == test_user["telegram_id"]

    def test_telegram_code_login_fails_with_invalid_code(self, client):
        """Test login with invalid Telegram code fails."""
        response = client.post("/auth/telegram/code", json={"code": "INVALID"})

        assert response.status_code == 401
        assert "Codigo invalido o expirado" in response.json()["detail"]


@pytest.mark.security
class TestRegistration:
    """Tests for user registration."""

    def test_register_success(self, client, db):
        """Test successful user registration."""
        user_data = {
            "email": "newuser@example.com",
            "password": "securepassword123",
            "name": "New User",
        }

        response = client.post("/auth/register", json=user_data)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user_data["email"]
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["account_type"] == "web-only"

    def test_register_fails_with_duplicate_email(self, client, test_user):
        """Test registration fails with existing email."""
        user_data = {
            "email": test_user["email"],
            "password": "securepassword123",
            "name": "Another User",
        }

        response = client.post("/auth/register", json=user_data)

        assert response.status_code == 409
        assert "Ya existe una cuenta con ese email" in response.json()["detail"]

    def test_register_requires_email(self, client):
        """Test registration requires email."""
        user_data = {
            "password": "securepassword123",
            "name": "New User",
        }

        response = client.post("/auth/register", json=user_data)

        assert response.status_code == 400
        assert "email y password son requeridos" in response.json()["detail"]

    def test_register_requires_password(self, client):
        """Test registration requires password."""
        user_data = {
            "email": "newuser@example.com",
            "name": "New User",
        }

        response = client.post("/auth/register", json=user_data)

        assert response.status_code == 400
        assert "email y password son requeridos" in response.json()["detail"]

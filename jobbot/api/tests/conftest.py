"""
Shared fixtures and configuration for JobBot API tests.
"""

import hashlib
import os
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

os.environ["JWT_SECRET_KEY"] = "test-secret-key-min-32-chars-long-for-testing"
os.environ["APP_ENV"] = "testing"
os.environ["TELEGRAM_BOT_TOKEN"] = "test_bot_token"

from fastapi.testclient import TestClient

from api.main import app
from api.core.security import (
    create_access_token,
    create_refresh_token,
    TokenBlacklist,
    RefreshTokenManager,
    hash_token,
)
from api.rate_limit import (
    InMemoryRateLimiter,
    EndpointRateLimiter,
    RateLimitCategory,
)


try:
    from job_bot.database import Database
except ImportError:
    from database import Database


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def db():
    """Create a test database instance with in-memory SQLite."""
    return Database(db_path=":memory:")


@pytest.fixture
def token_blacklist(db):
    """Create a token blacklist instance."""
    return TokenBlacklist(db)


@pytest.fixture
def refresh_manager(db):
    """Create a refresh token manager instance."""
    return RefreshTokenManager(db)


@pytest.fixture
def test_user(db):
    """Create a test user in the database."""
    telegram_id = 123456789
    email = "test@example.com"
    password = "testpassword123"

    db.create_user_if_not_exists(telegram_id, "Test User")
    db.create_web_user(telegram_id, email, password)

    return {
        "telegram_id": telegram_id,
        "email": email,
        "password": password,
        "name": "Test User",
    }


@pytest.fixture
def auth_token_pair(test_user, refresh_manager):
    """Create a valid access and refresh token pair for the test user."""
    access_token, refresh_token = refresh_manager.create_refresh_token_pair(
        user_id=test_user["telegram_id"],
        email=test_user["email"],
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "telegram_id": test_user["telegram_id"],
        "email": test_user["email"],
    }


@pytest.fixture
def auth_headers(auth_token_pair):
    """Create authorization headers with valid token."""
    return {"Authorization": f"Bearer {auth_token_pair['access_token']}"}


@pytest.fixture
def expired_token(test_user):
    """Create an expired access token."""
    return create_access_token(
        data={
            "sub": test_user["email"],
            "telegram_id": test_user["telegram_id"],
        },
        expires_delta=timedelta(seconds=-1),  # Expired 1 second ago
    )


@pytest.fixture
def invalid_token():
    """Create an invalid token."""
    return "invalid.token.here"


@pytest.fixture
def mock_stripe():
    """Create a mock for Stripe API."""
    with patch("api.routes.subscriptions.stripe") as mock:
        yield mock


@pytest.fixture
def mock_mercadopago():
    """Create a mock for MercadoPago SDK."""
    with patch("api.routes.subscriptions.mercadopago") as mock:
        yield mock


@pytest.fixture
def stripe_webhook_secret():
    """Stripe webhook secret for testing."""
    return "whsec_test_secret_key_for_testing_webhooks"


@pytest.fixture
def mercadopago_webhook_secret():
    """MercadoPago webhook secret for testing."""
    return "mp_test_webhook_secret"


@pytest.fixture
def valid_stripe_event():
    """Create a valid Stripe webhook event."""
    return {
        "id": "evt_test_1234567890",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_1234567890",
                "metadata": {
                    "telegram_id": "123456789",
                    "plan": "pro",
                },
                "subscription": "sub_test_1234567890",
            }
        },
    }


@pytest.fixture
def valid_mp_payment():
    """Create a valid MercadoPago payment object."""
    return {
        "id": "123456789",
        "status": "approved",
        "metadata": {
            "telegram_id": "123456789",
            "plan": "pro",
        },
    }


@pytest.fixture
def rate_limiter():
    """Create a fresh in-memory rate limiter."""
    return InMemoryRateLimiter()


@pytest.fixture
def endpoint_limiter():
    """Create a fresh endpoint rate limiter."""
    limiter = EndpointRateLimiter()
    # Reset the global limiter
    limiter._limiter._events.clear()
    return limiter


@pytest.fixture
def clean_rate_limits():
    """Reset rate limiters before test."""
    from api.rate_limit import endpoint_rate_limiter, rate_limiter

    endpoint_rate_limiter._limiter._events.clear()
    rate_limiter._events.clear()
    yield
    # Cleanup after test
    endpoint_rate_limiter._limiter._events.clear()
    rate_limiter._events.clear()


@pytest.fixture
def telegram_auth_data():
    """Valid Telegram authentication data for testing."""
    import time

    auth_date = int(time.time())
    telegram_id = 123456789
    first_name = "Test"

    # Create a valid hash for testing
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "test_bot_token")
    check_pairs = {
        "auth_date": str(auth_date),
        "first_name": first_name,
        "id": str(telegram_id),
    }
    data_check_string = "\n".join(
        f"{key}={value}" for key, value in sorted(check_pairs.items())
    )
    secret_key = hashlib.sha256(token.encode()).digest()
    hash_value = hashlib.sha256(secret_key + data_check_string.encode()).hexdigest()

    return {
        "telegram_id": telegram_id,
        "auth_date": auth_date,
        "telegram_first_name": first_name,
        "telegram_last_name": "User",
        "telegram_username": "testuser",
        "hash": hash_value,
    }


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "security: marks tests as security tests")
    config.addinivalue_line("markers", "webhook: marks tests as webhook tests")
    config.addinivalue_line("markers", "payment: marks tests as payment tests")


def pytest_collection_modifyitems(config, items):
    """Add markers to test items based on their name."""
    for item in items:
        if "webhook" in item.nodeid.lower():
            item.add_marker(pytest.mark.webhook)
        if (
            "payment" in item.nodeid.lower()
            or "stripe" in item.nodeid.lower()
            or "mercadopago" in item.nodeid.lower()
        ):
            item.add_marker(pytest.mark.payment)
        if "security" in item.nodeid.lower() or "auth" in item.nodeid.lower():
            item.add_marker(pytest.mark.security)

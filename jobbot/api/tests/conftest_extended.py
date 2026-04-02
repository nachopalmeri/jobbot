"""
Additional conftest fixtures for comprehensive testing
"""

import os
import sys
import hashlib
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

# Add jobbot to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

os.environ["JWT_SECRET_KEY"] = "test-secret-key-min-32-chars-long-for-testing"
os.environ["APP_ENV"] = "testing"
os.environ["TELEGRAM_BOT_TOKEN"] = "test_bot_token_123456789"
os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test_secret_key_for_testing_webhooks"
os.environ["MP_WEBHOOK_SECRET"] = "mp_test_webhook_secret"
os.environ["STRIPE_SECRET_KEY"] = "sk_test_secret_key"
os.environ["MP_ACCESS_TOKEN"] = "test_access_token"
os.environ["GROQ_API_KEY"] = "test_groq_key"

from fastapi.testclient import TestClient
from api.main import app
from api.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
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


# ============================================================================
# Core Fixtures
# ============================================================================


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
        expires_delta=timedelta(seconds=-1),
    )


@pytest.fixture
def invalid_token():
    """Create an invalid token."""
    return "invalid.token.here"


# ============================================================================
# Mock Fixtures
# ============================================================================


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
def mock_groq():
    """Create a mock for Groq API."""
    with patch("api.routes.cv.requests.post") as mock:
        mock.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "choices": [
                    {
                        "message": {
                            "content": '{"match_score": 85, "fit": "Good fit", "reasoning": "Test"}'
                        }
                    }
                ]
            },
        )
        yield mock


@pytest.fixture
def mock_job_scraper():
    """Create a mock for JobScraper."""
    with patch("api.routes.jobs.JobScraper") as mock_class:
        mock_instance = MagicMock()
        mock_instance.search_jobs.return_value = [
            {
                "id": f"job_{i}",
                "title": f"Python Developer {i}",
                "company": "TechCorp",
                "location": "Remote",
                "url": f"https://example.com/job{i}",
                "description": "Python, FastAPI",
                "date": datetime.now(timezone.utc).isoformat(),
            }
            for i in range(5)
        ]
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_cv_analyzer():
    """Create a mock for CV analyzer."""
    with patch("api.routes.cv.parse_cv") as mock:
        mock.return_value = "Python developer with 5 years experience"
        yield mock


# ============================================================================
# Webhook Fixtures
# ============================================================================


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


# ============================================================================
# Rate Limiting Fixtures
# ============================================================================


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


# ============================================================================
# Telegram Fixtures
# ============================================================================


@pytest.fixture
def telegram_auth_data():
    """Valid Telegram authentication data for testing."""
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
    hash_value = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    return {
        "telegram_id": telegram_id,
        "auth_date": auth_date,
        "telegram_first_name": first_name,
        "telegram_last_name": "User",
        "telegram_username": "testuser",
        "hash": hash_value,
    }


# ============================================================================
# Data Fixtures
# ============================================================================


@pytest.fixture
def test_job_data():
    """Create test job data."""
    return {
        "id": f"job_{datetime.now().timestamp()}",
        "title": "Senior Python Developer",
        "company": "TechCorp",
        "location": "Remote",
        "url": "https://example.com/job/123",
        "description": "Python, FastAPI, PostgreSQL, Docker",
        "salary_min": 80000,
        "salary_max": 120000,
        "currency": "USD",
        "date": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
def test_application_data():
    """Create test job application data."""
    return {
        "job_title": "Senior Python Developer",
        "company": "TechCorp",
        "url": "https://example.com/job/123",
        "notes": "Applied via company website",
    }


@pytest.fixture
def test_preferences_data():
    """Create test user preferences data."""
    return {
        "experience_level": "senior",
        "role_type": "Backend Developer",
        "technologies": "Python, FastAPI, PostgreSQL",
        "job_modality": "remoto",
        "max_job_age_days": 7,
        "match_threshold": 75,
        "alert_channel": "telegram",
        "check_interval_hours": 6,
        "alert_start_hour": 8,
        "alert_end_hour": 22,
        "timezone": "America/Buenos_Aires",
        "weekly_goal": 10,
        "digest_mode": "realtime",
        "active_alerts": True,
        "blocked_companies": "",
        "preferred_companies": "",
    }


# ============================================================================
# Pytest Configuration
# ============================================================================


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "security: marks tests as security tests")
    config.addinivalue_line("markers", "webhook: marks tests as webhook tests")
    config.addinivalue_line("markers", "payment: marks tests as payment tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")
    config.addinivalue_line("markers", "edge_cases: marks tests as edge case tests")
    config.addinivalue_line("markers", "contract: marks tests as contract tests")
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests")


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
        if "performance" in item.nodeid.lower() or "load" in item.nodeid.lower():
            item.add_marker(pytest.mark.performance)
        if "edge" in item.nodeid.lower():
            item.add_marker(pytest.mark.edge_cases)
        if "contract" in item.nodeid.lower():
            item.add_marker(pytest.mark.contract)
        if "integration" in item.nodeid.lower():
            item.add_marker(pytest.mark.integration)

"""
Test Utilities for JobBot API Tests
"""

import os
import tempfile
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from unittest.mock import MagicMock


class TestDataFactory:
    """Factory for creating test data."""

    @staticmethod
    def create_test_user(telegram_id: int = None, email: str = None) -> Dict[str, Any]:
        """Create test user data."""
        return {
            "telegram_id": telegram_id or 123456789,
            "email": email or f"test_{telegram_id}@example.com",
            "password": "SecurePass123!",
            "name": "Test User",
        }

    @staticmethod
    def create_test_job(job_id: str = None) -> Dict[str, Any]:
        """Create test job data."""
        return {
            "id": job_id or f"job_{datetime.now().timestamp()}",
            "title": "Senior Python Developer",
            "company": "TechCorp",
            "location": "Remote",
            "url": f"https://example.com/job/{job_id}",
            "description": "Python, FastAPI, PostgreSQL, Docker",
            "date": datetime.now(timezone.utc).isoformat(),
            "salary_min": 80000,
            "salary_max": 120000,
            "currency": "USD",
        }

    @staticmethod
    def create_test_application(job_title: str = "Test Job") -> Dict[str, Any]:
        """Create test job application data."""
        return {
            "job_title": job_title,
            "company": "TestCorp",
            "url": "https://example.com/job/123",
            "notes": "Applied via company website",
        }

    @staticmethod
    def create_stripe_event(
        event_type: str = "checkout.session.completed",
    ) -> Dict[str, Any]:
        """Create test Stripe webhook event."""
        return {
            "id": f"evt_{datetime.now().timestamp()}",
            "type": event_type,
            "data": {
                "object": {
                    "id": f"cs_{datetime.now().timestamp()}",
                    "metadata": {
                        "telegram_id": "123456789",
                        "plan": "pro",
                    },
                    "subscription": f"sub_{datetime.now().timestamp()}",
                }
            },
        }

    @staticmethod
    def create_telegram_auth_data(telegram_id: int = 123456789) -> Dict[str, Any]:
        """Create test Telegram auth data."""
        import time
        import hashlib

        auth_date = int(time.time())
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


class MockFactory:
    """Factory for creating mocks."""

    @staticmethod
    def create_stripe_mock():
        """Create mock Stripe SDK."""
        mock = MagicMock()
        mock.checkout.Session.create.return_value = MagicMock(
            url="https://checkout.stripe.com/test_session",
            id="cs_test_123",
        )
        return mock

    @staticmethod
    def create_mercadopago_mock():
        """Create mock MercadoPago SDK."""
        mock_sdk = MagicMock()
        mock_preference = MagicMock()
        mock_preference.create.return_value = {
            "response": {
                "init_point": "https://mp.com/checkout/test",
                "id": "pref_test_123",
            }
        }
        mock_sdk.preference.return_value = mock_preference
        return mock_sdk

    @staticmethod
    def create_groq_mock():
        """Create mock Groq API response."""
        return {
            "choices": [
                {"message": {"content": '{"match_score": 85, "fit": "Good fit"}'}}
            ]
        }

    @staticmethod
    def create_job_scraper_mock(jobs_count: int = 5):
        """Create mock JobScraper."""
        mock = MagicMock()
        mock.search_jobs.return_value = [
            {
                "id": f"job_{i}",
                "title": f"Job {i}",
                "company": "TestCorp",
                "url": f"https://example.com/job{i}",
            }
            for i in range(jobs_count)
        ]
        return mock


class TestFileFactory:
    """Factory for creating test files."""

    @staticmethod
    def create_test_cv(
        content: str = "Python Developer with 5 years experience",
    ) -> tuple:
        """Create a test CV file."""
        fd, path = tempfile.mkstemp(suffix=".pdf")
        with os.fdopen(fd, "w") as f:
            f.write(content)
        return path, content

    @staticmethod
    def create_test_pdf(size_bytes: int = 1024) -> tuple:
        """Create a test PDF file of specified size."""
        fd, path = tempfile.mkstemp(suffix=".pdf")
        with os.fdopen(fd, "wb") as f:
            f.write(b"%PDF-1.4\n" + b"x" * (size_bytes - 10))
        return path, size_bytes

    @staticmethod
    def cleanup_file(path: str):
        """Clean up test file."""
        if os.path.exists(path):
            os.unlink(path)


class AssertionHelpers:
    """Helper methods for common assertions."""

    @staticmethod
    def assert_valid_token_response(response_data: Dict[str, Any]):
        """Assert response contains valid token data."""
        assert "access_token" in response_data
        assert "token_type" in response_data
        assert response_data["token_type"].lower() == "bearer"
        assert len(response_data["access_token"].split(".")) == 3

    @staticmethod
    def assert_valid_user_response(
        response_data: Dict[str, Any], expected_email: str = None
    ):
        """Assert response contains valid user data."""
        assert "telegram_id" in response_data
        assert "email" in response_data
        if expected_email:
            assert response_data["email"] == expected_email

    @staticmethod
    def assert_valid_health_response(response_data: Dict[str, Any]):
        """Assert response contains valid health data."""
        assert "status" in response_data
        assert "timestamp" in response_data
        assert "version" in response_data
        assert response_data["status"] in ["healthy", "degraded", "unhealthy"]

    @staticmethod
    def assert_rate_limit_headers(headers: Dict[str, str]):
        """Assert rate limit headers are present."""
        assert any(h in headers for h in ["X-RateLimit-Limit", "x-ratelimit-limit"]), (
            "Missing rate limit headers"
        )

    @staticmethod
    def assert_security_headers(headers: Dict[str, str]):
        """Assert security headers are present."""
        security_headers = [
            "x-content-type-options",
            "x-frame-options",
            "strict-transport-security",
        ]

        header_keys_lower = {k.lower() for k in headers.keys()}
        present = sum(1 for h in security_headers if h in header_keys_lower)
        assert present >= 2, f"Only {present}/3 security headers present"


def generate_sql_injection_payloads() -> list:
    """Generate common SQL injection payloads."""
    return [
        "' OR '1'='1",
        "admin'--",
        "' OR 1=1--",
        "'; DROP TABLE users; --",
        "' UNION SELECT * FROM users--",
        "1' AND 1=1--",
    ]


def generate_xss_payloads() -> list:
    """Generate common XSS payloads."""
    return [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert('xss')>",
        "javascript:alert('xss')",
        "<svg onload=alert('xss')>",
        "<iframe src='javascript:alert(1)'>",
        "<body onload=alert('xss')>",
    ]


def generate_malicious_file_names() -> list:
    """Generate malicious file names for testing."""
    return [
        "../../../etc/passwd.pdf",
        "file.pdf\x00.exe",
        "..\\..\\windows\\system32\\file.pdf",
        "file.pdf; rm -rf /",
        "<script>alert(1)</script>.pdf",
    ]

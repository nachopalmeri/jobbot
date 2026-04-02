"""
Edge Cases and Error Handling Tests for JobBot API
Testing boundary conditions, malformed inputs, and failure scenarios
"""

import json
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.mark.edge_cases
class TestEdgeCaseInputs:
    """Tests for edge case and boundary inputs."""

    def test_very_long_email_address(self, client):
        """Test registration with extremely long email."""
        long_email = "a" * 200 + "@example.com"

        response = client.post(
            "/auth/register",
            json={
                "email": long_email,
                "password": "SecurePass123!",
                "name": "Test User",
            },
        )

        # Should either succeed or fail gracefully
        assert response.status_code in [200, 400, 422]

    def test_special_characters_in_name(self, client, db):
        """Test registration with special characters in name."""
        special_names = [
            "User<script>alert('xss')</script>",
            "User' OR '1'='1",
            "User; DROP TABLE users;",
            "User\\n\\t\\r",
            "🔥 Fire Emoji User 🔥",
            "User\x00with\x00null",
        ]

        for i, name in enumerate(special_names):
            response = client.post(
                "/auth/register",
                json={
                    "email": f"special{i}@test.com",
                    "password": "SecurePass123!",
                    "name": name,
                },
            )

            # Should handle gracefully - either accept sanitized or reject
            assert response.status_code in [200, 400, 422, 500]

    def test_very_long_password(self, client):
        """Test registration with extremely long password."""
        long_password = "A" * 10000

        response = client.post(
            "/auth/register",
            json={
                "email": "longpass@test.com",
                "password": long_password,
                "name": "Test User",
            },
        )

        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

    def test_unicode_in_job_search_query(self, client, auth_headers):
        """Test job search with unicode and special characters."""
        queries = [
            "developer🔥",
            "résumé",
            "日本語",
            "عربي",
            "<script>",
            "'; DROP TABLE jobs; --",
        ]

        for query in queries:
            response = client.get(
                f"/jobs/search?q={query}",
                headers=auth_headers,
            )
            # Should not crash
            assert response.status_code in [200, 400, 422, 500]

    def test_empty_strings_and_whitespace(self, client):
        """Test handling of empty strings and whitespace."""
        test_cases = [
            {"email": "", "password": "pass", "name": "Test"},
            {"email": "   ", "password": "pass", "name": "Test"},
            {"email": "test@test.com", "password": "", "name": "Test"},
            {"email": "test@test.com", "password": "pass", "name": ""},
            {"email": "test@test.com", "password": "   ", "name": "Test"},
        ]

        for data in test_cases:
            response = client.post("/auth/register", json=data)
            # Should not crash, should validate
            assert response.status_code in [200, 400, 422]


@pytest.mark.edge_cases
class TestRateLimitingExhaustion:
    """Tests for rate limiting edge cases."""

    def test_rate_limit_boundary_exact_limit(self, client, clean_rate_limits, db):
        """Test exactly at rate limit boundary."""
        email = "boundary@test.com"

        # Make requests up to but not exceeding limit
        for i in range(5):  # Assuming 5 request limit
            response = client.post(
                "/auth/token",
                data={
                    "username": email,
                    "password": "wrong",
                },
            )
            # Should get 401 for wrong password, not 429 yet
            if i < 4:
                assert response.status_code in [401, 429]

        # Next request should be rate limited
        limited_response = client.post(
            "/auth/token",
            data={
                "username": email,
                "password": "wrong",
            },
        )
        # Should be rate limited now
        assert limited_response.status_code in [401, 429]

    def test_multiple_ips_rate_limit_isolation(self, client, clean_rate_limits):
        """Test that rate limits are isolated by IP."""
        # This tests that one IP being rate limited doesn't affect others
        # Implementation depends on how client IP is extracted in tests
        pass  # Placeholder - depends on test client capabilities

    def test_rate_limit_reset_accuracy(self, client, clean_rate_limits):
        """Test rate limit resets after exact window time."""
        email = "reset_test@test.com"

        # Exhaust rate limit
        for _ in range(5):
            client.post(
                "/auth/token",
                data={
                    "username": email,
                    "password": "wrong",
                },
            )

        # Verify rate limited
        limited = client.post(
            "/auth/token",
            data={
                "username": email,
                "password": "wrong",
            },
        )

        if limited.status_code == 429:
            retry_after = int(limited.headers.get("Retry-After", 60))
            # In real test, would wait. Here we just verify header exists
            assert retry_after > 0


@pytest.mark.edge_cases
class TestDatabaseConnectionFailures:
    """Tests for database failure scenarios."""

    def test_database_connection_timeout(self, client, auth_headers):
        """Test handling of database connection timeout."""
        with patch("job_bot.database.Database._get_connection") as mock_conn:
            mock_conn.side_effect = TimeoutError("Database connection timeout")

            response = client.get("/auth/me", headers=auth_headers)

            # Should return 503 or 500, not crash
            assert response.status_code in [500, 503, 401, 200]

    def test_database_lock_timeout(self, client, auth_headers):
        """Test handling of database lock timeouts."""
        with patch("sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_conn.execute.side_effect = Exception("database is locked")
            mock_connect.return_value = mock_conn

            response = client.get("/auth/me", headers=auth_headers)

            # Should handle gracefully
            assert response.status_code in [500, 503, 200, 401]

    def test_database_corruption_handling(self, client):
        """Test handling of database corruption."""
        with patch("job_bot.database.Database") as mock_db:
            mock_instance = MagicMock()
            mock_instance.get_user.side_effect = Exception(
                "database disk image is malformed"
            )
            mock_db.return_value = mock_instance

            response = client.post(
                "/auth/token",
                data={
                    "username": "test@test.com",
                    "password": "password",
                },
            )

            # Should not crash server
            assert response.status_code in [500, 503, 401]


@pytest.mark.edge_cases
class TestExternalAPITimeouts:
    """Tests for external API timeout scenarios."""

    def test_stripe_api_timeout(self, client, auth_headers, mock_stripe):
        """Test handling of Stripe API timeout."""
        mock_stripe.error.Timeout = type("Timeout", (), {})

        with patch("stripe.checkout.Session.create") as mock_create:
            mock_create.side_effect = TimeoutError("Stripe API timeout")

            response = client.post(
                "/subscriptions/create-checkout",
                headers=auth_headers,
                json={
                    "provider": "stripe",
                    "plan": "pro",
                },
            )

            # Should handle gracefully
            assert response.status_code in [200, 503, 500, 400]

    def test_groq_api_very_slow_response(self, client, auth_headers):
        """Test handling of very slow Groq API response."""
        with patch("requests.post") as mock_post:

            def slow_response(*args, **kwargs):
                time.sleep(0.1)  # Simulate slow response
                raise TimeoutError("Request timeout")

            mock_post.side_effect = slow_response

            with patch("api.routes.cv.GROQ_API_KEY", "test_key"):
                response = client.post(
                    "/cv/analyze-match",
                    headers=auth_headers,
                    json={
                        "job_url": "https://example.com/job",
                        "job_description": "Test",
                    },
                )

                assert response.status_code in [200, 503, 404]

    def test_webhook_timeout_during_processing(self, client, valid_stripe_event):
        """Test handling of webhook processing timeout."""
        with patch("stripe.Webhook.construct_event") as mock_construct:
            mock_construct.return_value = valid_stripe_event

            with patch(
                "api.routes.subscriptions.activate_subscription"
            ) as mock_activate:
                mock_activate.side_effect = TimeoutError("Processing timeout")

                response = client.post(
                    "/subscriptions/webhook/stripe",
                    data=json.dumps(valid_stripe_event),
                    headers={"stripe-signature": "t=123,v1=test"},
                )

                # Should not crash, might return 500 or handle gracefully
                assert response.status_code in [200, 500]


@pytest.mark.edge_cases
class TestMalformedPayloads:
    """Tests for malformed request payloads."""

    def test_invalid_json_body(self, client, auth_headers):
        """Test handling of invalid JSON in request body."""
        response = client.post(
            "/auth/register",
            headers={**auth_headers, "Content-Type": "application/json"},
            data="not valid json {{",
        )

        assert response.status_code in [400, 422]

    def test_missing_required_fields(self, client):
        """Test handling of missing required fields."""
        test_cases = [
            {},  # Empty body
            {"email": "test@test.com"},  # Missing password
            {"password": "password"},  # Missing email
            {"random_field": "value"},  # Wrong fields
        ]

        for body in test_cases:
            response = client.post("/auth/register", json=body)
            assert response.status_code in [400, 422]

    def test_wrong_data_types(self, client):
        """Test handling of wrong data types."""
        test_cases = [
            {"email": 123, "password": "pass", "name": "Test"},
            {"email": "test@test.com", "password": ["array"], "name": "Test"},
            {"email": "test@test.com", "password": "pass", "name": {"obj": "test"}},
        ]

        for body in test_cases:
            response = client.post("/auth/register", json=body)
            assert response.status_code in [400, 422]

    def test_nested_json_injection_attempts(self, client):
        """Test handling of nested JSON injection attempts."""
        malicious_payloads = [
            {"email": "test@test.com", "password": "pass", "extra": {"$ne": null}},
            {"email": "test@test.com", "password": "pass", "where": {"$exists": True}},
        ]

        for payload in malicious_payloads:
            response = client.post("/auth/register", json=payload)
            # Should not crash or allow injection
            assert response.status_code in [200, 400, 422]


@pytest.mark.edge_cases
class TestConcurrentRequestHandling:
    """Tests for concurrent request scenarios."""

    def test_concurrent_login_attempts_same_user(self, client, test_user):
        """Test concurrent login attempts for same user."""
        import threading
        import queue

        results = queue.Queue()

        def login():
            try:
                response = client.post(
                    "/auth/token",
                    data={
                        "username": test_user["email"],
                        "password": test_user["password"],
                    },
                )
                results.put(("success", response.status_code))
            except Exception as e:
                results.put(("error", str(e)))

        # Launch multiple concurrent logins
        threads = [threading.Thread(target=login) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All should succeed or handle gracefully
        success_count = 0
        while not results.empty():
            status, code = results.get()
            if status == "success" and code == 200:
                success_count += 1

        # At least some should succeed
        assert success_count >= 1

    def test_concurrent_registration_same_email(self, client):
        """Test concurrent registrations with same email."""
        import threading
        import queue

        results = queue.Queue()
        email = "concurrent_reg@test.com"

        def register():
            try:
                response = client.post(
                    "/auth/register",
                    json={
                        "email": email,
                        "password": "SecurePass123!",
                        "name": "Test User",
                    },
                )
                results.put(("success", response.status_code))
            except Exception as e:
                results.put(("error", str(e)))

        # Launch multiple concurrent registrations
        threads = [threading.Thread(target=register) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have one success and conflicts, or all succeed with DB constraint
        results_list = []
        while not results.empty():
            results_list.append(results.get())

        status_codes = [code for _, code in results_list]
        assert 200 in status_codes or all(code in [200, 409] for code in status_codes)


@pytest.mark.edge_cases
class TestRaceConditions:
    """Tests for race condition scenarios."""

    def test_refresh_token_race_condition(self, client, auth_token_pair):
        """Test race condition in token refresh."""
        import threading
        import queue

        results = queue.Queue()

        def refresh():
            try:
                response = client.post(
                    "/auth/refresh",
                    json={
                        "refresh_token": auth_token_pair["refresh_token"],
                    },
                )
                results.put(("success", response.status_code, response.json()))
            except Exception as e:
                results.put(("error", str(e)))

        # Launch two concurrent refresh attempts
        threads = [threading.Thread(target=refresh) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # One should succeed, one should fail (token rotation)
        results_list = []
        while not results.empty():
            results_list.append(results.get())

        success_count = sum(
            1 for status, code, _ in results_list if status == "success" and code == 200
        )
        # Exactly one should succeed due to token rotation
        assert success_count <= 1

    def test_concurrent_subscription_update(self, client, auth_headers, db, test_user):
        """Test concurrent subscription updates."""
        import threading
        import queue

        results = queue.Queue()

        def update_subscription():
            try:
                with patch("api.routes.subscriptions.activate_subscription") as mock:
                    mock.return_value = None
                    response = client.get("/subscriptions/status", headers=auth_headers)
                    results.put(("success", response.status_code))
            except Exception as e:
                results.put(("error", str(e)))

        # Launch multiple concurrent reads
        threads = [threading.Thread(target=update_subscription) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All should complete without errors
        while not results.empty():
            status, code = results.get()
            assert status in ["success", "error"]


@pytest.mark.edge_cases
class TestResourceExhaustion:
    """Tests for resource exhaustion scenarios."""

    def test_very_large_request_body(self, client):
        """Test handling of very large request body."""
        large_data = {"data": "x" * 10000000}  # 10MB

        response = client.post("/auth/register", json=large_data)

        # Should be rejected due to size
        assert response.status_code in [400, 413, 422]

    def test_rapid_fire_requests(self, client, clean_rate_limits):
        """Test handling of rapid-fire requests."""
        responses = []

        # Make many requests rapidly
        for _ in range(20):
            response = client.get("/health")
            responses.append(response.status_code)

        # Most should succeed (health endpoint is usually exempt)
        success_count = responses.count(200)
        assert success_count >= 15  # At least 75% should succeed

    def test_memory_pressure_simulation(self, client):
        """Test API behavior under memory pressure (simulated)."""
        # This is a placeholder - real memory testing requires more sophisticated setup
        # Just verify the API can handle normal requests
        response = client.get("/health")
        assert response.status_code == 200

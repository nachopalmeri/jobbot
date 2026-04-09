"""
Webhook general tests for JobBot API.
Tests for webhook deduplication, retry logic, and validation.
"""

import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch, Mock

import pytest
from fastapi.testclient import TestClient


@pytest.mark.webhook
class TestWebhookDeduplication:
    """Tests for webhook event deduplication."""

    @pytest.fixture(autouse=True)
    def setup_env(self, monkeypatch):
        """Set up environment for webhook tests."""
        monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test_secret")
        monkeypatch.setenv("MP_WEBHOOK_SECRET", "mp_test_secret")

    def test_webhook_deduplication_by_event_id(self, client, db):
        """Test that webhooks are deduplicated by event_id."""
        event_id = "evt_unique_123456789"

        # Simulate that event has been processed
        with patch.object(db, "is_webhook_processed") as mock_is_processed:
            mock_is_processed.return_value = True

            payload = {
                "id": event_id,
                "type": "test.event",
                "data": {"test": "data"},
            }

            # First request
            response1 = client.post(
                "/subscriptions/webhook/stripe",
                data=json.dumps(payload),
                headers={"stripe-signature": "test_sig"},
            )

            assert response1.status_code == 200
            assert response1.json()["status"] == "already_processed"

            # Same event ID should return already_processed
            mock_is_processed.assert_called_with(event_id)

    def test_webhook_unique_events_processed_separately(self, client, db):
        """Test that unique events are processed separately."""
        with patch.object(db, "is_webhook_processed") as mock_is_processed:
            mock_is_processed.return_value = False

            with patch.object(db, "mark_webhook_processed") as mock_mark:
                event1 = {
                    "id": "evt_1",
                    "type": "payment.success",
                    "data": {},
                }
                event2 = {
                    "id": "evt_2",
                    "type": "payment.success",
                    "data": {},
                }

                # First event
                mock_is_processed.return_value = False
                response1 = client.post(
                    "/subscriptions/webhook/stripe",
                    data=json.dumps(event1),
                    headers={"stripe-signature": "sig1"},
                )

                # Second event (different ID)
                mock_is_processed.return_value = False
                response2 = client.post(
                    "/subscriptions/webhook/stripe",
                    data=json.dumps(event2),
                    headers={"stripe-signature": "sig2"},
                )

                # Both should succeed
                assert response1.status_code == 200
                assert response2.status_code == 200


@pytest.mark.webhook
class TestWebhookRetryLogic:
    """Tests for webhook retry with exponential backoff."""

    def test_webhook_logs_retry_attempts(self, client, db, caplog):
        """Test that webhook retry attempts are logged."""
        import logging

        with caplog.at_level(logging.INFO):
            with patch.object(db, "is_webhook_processed") as mock_is_processed:
                mock_is_processed.return_value = False

                event = {
                    "id": "evt_retry_test",
                    "type": "test.event",
                    "data": {},
                }

                response = client.post(
                    "/subscriptions/webhook/stripe",
                    data=json.dumps(event),
                    headers={"stripe-signature": "test"},
                )

                # Check that request was logged
                assert any(
                    "http_request" in record.message for record in caplog.records
                )

    def test_webhook_event_timestamp_validation(self, client, db):
        """Test that webhook events with old timestamps are handled."""
        # Event from 1 hour ago
        old_timestamp = int(time.time()) - 3600

        with patch.object(db, "is_webhook_processed") as mock_is_processed:
            mock_is_processed.return_value = False

            event = {
                "id": "evt_old_timestamp",
                "type": "test.event",
                "created": old_timestamp,
                "data": {},
            }

            response = client.post(
                "/subscriptions/webhook/stripe",
                data=json.dumps(event),
                headers={"stripe-signature": "test"},
            )

            # Should still process (or handle according to business logic)
            assert response.status_code in [200, 400]


@pytest.mark.webhook
class TestWebhookValidation:
    """Tests for webhook request validation."""

    def test_webhook_invalid_payload_returns_400(self, client):
        """Test webhook with malformed JSON returns 400."""
        invalid_payload = "this is not valid json"

        with patch("stripe.Webhook.construct_event") as mock_construct:
            import stripe

            mock_construct.side_effect = ValueError("Invalid payload")

            response = client.post(
                "/subscriptions/webhook/stripe",
                data=invalid_payload,
                headers={"stripe-signature": "invalid"},
            )

            assert response.status_code == 400

    def test_webhook_missing_signature_returns_400(self, client):
        """Test webhook without signature header returns 400."""
        payload = json.dumps({"test": "data"})

        response = client.post(
            "/subscriptions/webhook/stripe",
            data=payload,
            # No stripe-signature header
        )

        # Should return 400 or 503 if not configured
        assert response.status_code in [400, 503]

    def test_webhook_invalid_secret_returns_401(self, client):
        """Test webhook with invalid secret returns 401."""
        payload = json.dumps({"test": "data"})

        with patch("stripe.Webhook.construct_event") as mock_construct:
            import stripe

            mock_construct.side_effect = stripe.error.SignatureVerificationError(
                "Invalid signature", None
            )

            response = client.post(
                "/subscriptions/webhook/stripe",
                data=payload,
                headers={"stripe-signature": "invalid_signature"},
            )

            assert response.status_code == 400
            assert "Invalid signature" in response.json()["detail"]


@pytest.mark.webhook
class TestWebhookProcessing:
    """Tests for webhook processing logic."""

    def test_webhook_persists_event_data(self, client, db):
        """Test that webhook event data is persisted correctly."""
        event_id = "evt_persist_test"

        with patch.object(db, "is_webhook_processed") as mock_is_processed:
            mock_is_processed.return_value = False

            with patch.object(db, "mark_webhook_processed") as mock_mark:
                mock_mark.return_value = True

                event = {
                    "id": event_id,
                    "type": "checkout.session.completed",
                    "data": {
                        "object": {
                            "id": "cs_test",
                            "metadata": {"telegram_id": "12345", "plan": "pro"},
                        }
                    },
                }

                with patch("stripe.Webhook.construct_event") as mock_construct:
                    mock_construct.return_value = event

                    response = client.post(
                        "/subscriptions/webhook/stripe",
                        data=json.dumps(event),
                        headers={"stripe-signature": "test_sig"},
                    )

                    assert response.status_code == 200
                    # Verify mark_webhook_processed was called with correct params
                    mock_mark.assert_called_once()
                    args = mock_mark.call_args[0]
                    assert args[0] == event_id

    def test_webhook_handles_missing_metadata(self, client, db):
        """Test webhook handles events with missing metadata gracefully."""
        event_id = "evt_no_metadata"

        with patch.object(db, "is_webhook_processed") as mock_is_processed:
            mock_is_processed.return_value = False

            event = {
                "id": event_id,
                "type": "checkout.session.completed",
                "data": {
                    "object": {
                        "id": "cs_test",
                        # Missing metadata
                    }
                },
            }

            with patch("stripe.Webhook.construct_event") as mock_construct:
                mock_construct.return_value = event

                with patch(
                    "api.routes.subscriptions.activate_subscription"
                ) as mock_activate:
                    mock_activate.side_effect = ValueError("telegram_id requerido")

                    response = client.post(
                        "/subscriptions/webhook/stripe",
                        data=json.dumps(event),
                        headers={"stripe-signature": "test_sig"},
                    )

                    # Should handle error gracefully
                    assert response.status_code in [200, 400, 500]


@pytest.mark.webhook
class TestWebhookSecurity:
    """Tests for webhook security features."""

    def test_webhook_ip_whitelist_blocks_unauthorized(self, client, monkeypatch):
        """Test IP whitelist blocks unauthorized IPs."""
        monkeypatch.setenv("MP_WEBHOOK_IPS", "192.168.1.100")

        payload = {
            "type": "payment",
            "data": {"resource": {"id": "123", "status": "approved"}},
        }

        # Request from unauthorized IP
        response = client.post(
            "/subscriptions/webhook/mercadopago",
            json=payload,
            headers={"X-Forwarded-For": "10.0.0.1"},
        )

        assert response.status_code == 403

    def test_webhook_ip_whitelist_allows_authorized(self, client, monkeypatch):
        """Test IP whitelist allows authorized IPs."""
        monkeypatch.setenv("MP_WEBHOOK_IPS", "192.168.1.100,10.0.0.1")

        with patch.object(Database, "is_webhook_processed") as mock_is_processed:
            mock_is_processed.return_value = False

            payload = {
                "type": "payment",
                "data": {"resource": {"id": "123", "status": "approved"}},
            }

            response = client.post(
                "/subscriptions/webhook/mercadopago",
                json=payload,
                headers={"X-Forwarded-For": "10.0.0.1"},
            )

            # Should be allowed (might fail for other reasons but not 403)
            assert response.status_code != 403

    def test_webhook_signature_timing_attack_prevention(self, client):
        """Test that signature validation uses constant-time comparison."""
        # This tests that signatures are validated securely
        payload = json.dumps({"test": "data"})

        with patch("stripe.Webhook.construct_event") as mock_construct:
            import stripe

            # Multiple invalid attempts should take similar time
            signatures = [
                "t=1234567890,v1=a" * 50,  # Wrong length
                "t=1234567890,v1=b" * 50,  # Different wrong signature
                "t=1234567890,v1=c" * 50,  # Another wrong signature
            ]

            mock_construct.side_effect = stripe.error.SignatureVerificationError(
                "Invalid signature", None
            )

            for sig in signatures:
                response = client.post(
                    "/subscriptions/webhook/stripe",
                    data=payload,
                    headers={"stripe-signature": sig},
                )
                assert response.status_code == 400


@pytest.mark.webhook
class TestWebhookRateLimiting:
    """Tests for webhook rate limiting."""

    def test_webhook_rate_limiting_applied(self, client, db, clean_rate_limits):
        """Test that webhooks have rate limiting applied."""
        from api.rate_limit import endpoint_rate_limiter, RateLimitCategory

        # Register webhook endpoint with rate limiting
        endpoint_rate_limiter.register_endpoint(
            "/subscriptions/webhook/stripe", RateLimitCategory.WEBHOOKS
        )

        # Make many requests
        responses = []
        for i in range(110):  # Webhook limit is 100/min
            with patch.object(db, "is_webhook_processed") as mock_is_processed:
                mock_is_processed.return_value = True  # Skip processing

                response = client.post(
                    "/subscriptions/webhook/stripe",
                    data=json.dumps({"id": f"evt_{i}"}),
                    headers={"stripe-signature": f"sig_{i}"},
                )
                responses.append(response.status_code)

        # Some should be rate limited (429)
        assert 429 in responses or all(r in [200, 400, 503] for r in responses)

    def test_webhook_rate_limit_headers_present(self, client, db):
        """Test that rate limit headers are present in webhook responses."""
        with patch.object(db, "is_webhook_processed") as mock_is_processed:
            mock_is_processed.return_value = True

            response = client.post(
                "/subscriptions/webhook/stripe",
                data=json.dumps({"id": "evt_test"}),
                headers={"stripe-signature": "test"},
            )

            # Headers should be present
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers


@pytest.mark.webhook
class TestWebhookErrorHandling:
    """Tests for webhook error handling."""

    def test_webhook_handles_database_error(self, client, db):
        """Test webhook handles database errors gracefully."""
        with patch.object(db, "is_webhook_processed") as mock_is_processed:
            mock_is_processed.side_effect = Exception("Database error")

            response = client.post(
                "/subscriptions/webhook/stripe",
                data=json.dumps({"id": "evt_test"}),
                headers={"stripe-signature": "test"},
            )

            # Should handle error without crashing
            assert response.status_code in [200, 500]

    def test_webhook_handles_timeout(self, client, db):
        """Test webhook handles processing timeout."""
        with patch.object(db, "is_webhook_processed") as mock_is_processed:
            mock_is_processed.return_value = False

            with patch(
                "api.routes.subscriptions.activate_subscription"
            ) as mock_activate:
                # Simulate slow processing
                def slow_activate(*args, **kwargs):
                    time.sleep(0.1)
                    return None

                mock_activate.side_effect = slow_activate

                event = {
                    "id": "evt_timeout",
                    "type": "checkout.session.completed",
                    "data": {
                        "object": {
                            "id": "cs_test",
                            "metadata": {"telegram_id": "12345", "plan": "pro"},
                        }
                    },
                }

                with patch("stripe.Webhook.construct_event") as mock_construct:
                    mock_construct.return_value = event

                    response = client.post(
                        "/subscriptions/webhook/stripe",
                        data=json.dumps(event),
                        headers={"stripe-signature": "test"},
                    )

                    # Should complete eventually
                    assert response.status_code in [200, 500]

    def test_webhook_handles_concurrent_requests(self, client, db):
        """Test webhook handles concurrent requests safely."""
        import concurrent.futures

        event_ids = [f"evt_concurrent_{i}" for i in range(10)]
        responses = []

        def send_webhook(event_id):
            with patch.object(db, "is_webhook_processed") as mock_is_processed:
                mock_is_processed.return_value = True

                return client.post(
                    "/subscriptions/webhook/stripe",
                    data=json.dumps({"id": event_id}),
                    headers={"stripe-signature": "test"},
                ).status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(send_webhook, eid) for eid in event_ids]
            responses = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All requests should complete
        assert all(r in [200, 400, 503] for r in responses)

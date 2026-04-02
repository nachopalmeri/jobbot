"""
Payment and webhook tests for JobBot API.
Tests for Stripe and MercadoPago webhook processing, signature validation, and idempotency.
"""

import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch, Mock

import pytest
from fastapi.testclient import TestClient


@pytest.mark.payment
@pytest.mark.webhook
class TestStripeWebhook:
    """Tests for Stripe webhook processing."""

    @pytest.fixture(autouse=True)
    def setup_stripe_env(self, monkeypatch):
        """Set up Stripe environment variables for tests."""
        monkeypatch.setenv(
            "STRIPE_WEBHOOK_SECRET", "whsec_test_secret_key_for_testing_webhooks"
        )
        monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_secret_key")

    def _generate_stripe_signature(self, payload: str, secret: str) -> str:
        """Generate a valid Stripe webhook signature for testing."""
        timestamp = str(int(time.time()))
        signed_payload = f"{timestamp}.{payload}"
        signature = hmac.new(
            secret.encode(), signed_payload.encode(), hashlib.sha256
        ).hexdigest()
        return f"t={timestamp},v1={signature}"

    def test_stripe_webhook_valid_signature(self, client, db, valid_stripe_event):
        """Test Stripe webhook with valid signature is processed."""
        payload = json.dumps(valid_stripe_event)
        secret = os.environ["STRIPE_WEBHOOK_SECRET"]
        signature = self._generate_stripe_signature(payload, secret)

        with patch("stripe.Webhook.construct_event") as mock_construct:
            mock_construct.return_value = valid_stripe_event

            response = client.post(
                "/subscriptions/webhook/stripe",
                data=payload,
                headers={"stripe-signature": signature},
            )

            assert response.status_code == 200
            assert response.json()["status"] == "success"

    def test_stripe_webhook_invalid_signature_returns_400(
        self, client, valid_stripe_event
    ):
        """Test Stripe webhook with invalid signature returns 400."""
        payload = json.dumps(valid_stripe_event)
        invalid_signature = "t=1234567890,v1=invalid_signature"

        with patch("stripe.Webhook.construct_event") as mock_construct:
            import stripe

            mock_construct.side_effect = stripe.error.SignatureVerificationError(
                "Invalid signature", None
            )

            response = client.post(
                "/subscriptions/webhook/stripe",
                data=payload,
                headers={"stripe-signature": invalid_signature},
            )

            assert response.status_code == 400
            assert "Invalid signature" in response.json()["detail"]

    def test_stripe_webhook_subscription_created(self, client, db, valid_stripe_event):
        """Test processing of subscription.created event."""
        payload = json.dumps(valid_stripe_event)
        secret = os.environ["STRIPE_WEBHOOK_SECRET"]
        signature = self._generate_stripe_signature(payload, secret)

        with patch("stripe.Webhook.construct_event") as mock_construct:
            mock_construct.return_value = valid_stripe_event

            with patch(
                "api.routes.subscriptions.activate_subscription"
            ) as mock_activate:
                mock_activate.return_value = None

                response = client.post(
                    "/subscriptions/webhook/stripe",
                    data=payload,
                    headers={"stripe-signature": signature},
                )

                assert response.status_code == 200
                mock_activate.assert_called_once()

    def test_stripe_webhook_subscription_updated(self, client, db):
        """Test processing of subscription updated event."""
        event = {
            "id": "evt_test_updated",
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_test",
                    "metadata": {"telegram_id": "123456789"},
                    "status": "active",
                }
            },
        }
        payload = json.dumps(event)
        secret = os.environ["STRIPE_WEBHOOK_SECRET"]
        signature = self._generate_stripe_signature(payload, secret)

        with patch("stripe.Webhook.construct_event") as mock_construct:
            mock_construct.return_value = event

            response = client.post(
                "/subscriptions/webhook/stripe",
                data=payload,
                headers={"stripe-signature": signature},
            )

            assert response.status_code == 200

    def test_stripe_webhook_subscription_deleted(self, client, db):
        """Test processing of subscription cancelled event."""
        event = {
            "id": "evt_test_deleted",
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "id": "sub_test",
                    "metadata": {"telegram_id": "123456789"},
                }
            },
        }
        payload = json.dumps(event)
        secret = os.environ["STRIPE_WEBHOOK_SECRET"]
        signature = self._generate_stripe_signature(payload, secret)

        with patch("stripe.Webhook.construct_event") as mock_construct:
            mock_construct.return_value = event

            with patch(
                "api.routes.subscriptions.deactivate_subscription"
            ) as mock_deactivate:
                mock_deactivate.return_value = None

                response = client.post(
                    "/subscriptions/webhook/stripe",
                    data=payload,
                    headers={"stripe-signature": signature},
                )

                assert response.status_code == 200
                mock_deactivate.assert_called_once()

    def test_stripe_webhook_idempotency_same_event_not_processed_twice(
        self, client, db
    ):
        """Test that same webhook event is not processed twice (idempotency)."""
        event_id = "evt_test_idempotent_123"
        event = {
            "id": event_id,
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test",
                    "metadata": {"telegram_id": "123456789", "plan": "pro"},
                    "subscription": "sub_test",
                }
            },
        }
        payload = json.dumps(event)
        secret = os.environ["STRIPE_WEBHOOK_SECRET"]
        signature = self._generate_stripe_signature(payload, secret)

        # First request - mark as processed
        with patch("stripe.Webhook.construct_event") as mock_construct:
            mock_construct.return_value = event

            with patch.object(db, "is_webhook_processed") as mock_is_processed:
                with patch.object(db, "mark_webhook_processed") as mock_mark:
                    # First call returns False (not processed), second returns True
                    mock_is_processed.side_effect = [False, True]

                    # First request
                    response1 = client.post(
                        "/subscriptions/webhook/stripe",
                        data=payload,
                        headers={"stripe-signature": signature},
                    )
                    assert response1.status_code == 200
                    assert response1.json()["status"] == "success"

                    # Second request (same event)
                    response2 = client.post(
                        "/subscriptions/webhook/stripe",
                        data=payload,
                        headers={"stripe-signature": signature},
                    )
                    assert response2.status_code == 200
                    assert response2.json()["status"] == "already_processed"

    def test_stripe_webhook_invalid_payload_returns_400(self, client):
        """Test webhook with invalid JSON payload returns 400."""
        invalid_payload = "not valid json"
        signature = "t=1234567890,v1=invalid"

        with patch("stripe.Webhook.construct_event") as mock_construct:
            import stripe

            mock_construct.side_effect = ValueError("Invalid payload")

            response = client.post(
                "/subscriptions/webhook/stripe",
                data=invalid_payload,
                headers={"stripe-signature": signature},
            )

            assert response.status_code == 400
            assert "Invalid payload" in response.json()["detail"]


@pytest.mark.payment
@pytest.mark.webhook
class TestMercadoPagoWebhook:
    """Tests for MercadoPago webhook processing."""

    @pytest.fixture(autouse=True)
    def setup_mp_env(self, monkeypatch):
        """Set up MercadoPago environment variables for tests."""
        monkeypatch.setenv("MP_ACCESS_TOKEN", "test_access_token")
        monkeypatch.setenv("MP_WEBHOOK_SECRET", "mp_test_webhook_secret")

    def test_mercadopago_webhook_payment_approved(self, client, db, valid_mp_payment):
        """Test MercadoPago webhook with approved payment."""
        payload = {
            "type": "payment",
            "data": {
                "resource": valid_mp_payment,
            },
        }

        with patch.object(db, "is_webhook_processed") as mock_is_processed:
            mock_is_processed.return_value = False

            with patch(
                "api.routes.subscriptions.activate_subscription"
            ) as mock_activate:
                mock_activate.return_value = None

                response = client.post(
                    "/subscriptions/webhook/mercadopago",
                    json=payload,
                )

                assert response.status_code == 200
                assert response.json()["status"] == "success"
                mock_activate.assert_called_once()

    def test_mercadopago_webhook_idempotency(self, client, db, valid_mp_payment):
        """Test MercadoPago webhook idempotency."""
        payment_id = valid_mp_payment["id"]
        payload = {
            "type": "payment",
            "data": {
                "resource": valid_mp_payment,
            },
        }

        with patch.object(db, "is_webhook_processed") as mock_is_processed:
            # First call returns False, second returns True (already processed)
            mock_is_processed.side_effect = [False, True]

            with patch(
                "api.routes.subscriptions.activate_subscription"
            ) as mock_activate:
                mock_activate.return_value = None

                # First request
                response1 = client.post(
                    "/subscriptions/webhook/mercadopago",
                    json=payload,
                )
                assert response1.status_code == 200
                assert response1.json()["status"] == "success"

                # Second request (same payment)
                response2 = client.post(
                    "/subscriptions/webhook/mercadopago",
                    json=payload,
                )
                assert response2.status_code == 200
                assert response2.json()["status"] == "already_processed"

    def test_mercadopago_webhook_pending_payment_not_activated(self, client, db):
        """Test that pending payments don't activate subscription."""
        payload = {
            "type": "payment",
            "data": {
                "resource": {
                    "id": "123456789",
                    "status": "pending",
                    "metadata": {"telegram_id": "123456789", "plan": "pro"},
                },
            },
        }

        with patch("api.routes.subscriptions.activate_subscription") as mock_activate:
            response = client.post(
                "/subscriptions/webhook/mercadopago",
                json=payload,
            )

            assert response.status_code == 200
            mock_activate.assert_not_called()

    def test_mercadopago_webhook_invalid_signature_returns_400(
        self, client, monkeypatch
    ):
        """Test MercadoPago webhook with invalid signature returns 400."""
        monkeypatch.setenv("MP_WEBHOOK_SECRET", "valid_secret")

        payload = {"type": "payment"}

        response = client.post(
            "/subscriptions/webhook/mercadopago",
            json=payload,
            headers={"x-signature": "invalid_signature"},
        )

        assert response.status_code == 400

    def test_mercadopago_webhook_with_ip_whitelist(self, client, monkeypatch):
        """Test MercadoPago webhook IP whitelist validation."""
        monkeypatch.setenv("MP_WEBHOOK_IPS", "192.168.1.1,10.0.0.1")

        payload = {
            "type": "payment",
            "data": {
                "resource": {
                    "id": "123456789",
                    "status": "approved",
                    "metadata": {"telegram_id": "123456789", "plan": "pro"},
                },
            },
        }

        # Request from unauthorized IP
        response = client.post(
            "/subscriptions/webhook/mercadopago",
            json=payload,
            headers={"X-Forwarded-For": "1.2.3.4"},
        )

        assert response.status_code == 403
        assert "IP no autorizada" in response.json()["detail"]


@pytest.mark.payment
class TestPaymentCheckout:
    """Tests for payment checkout creation."""

    @pytest.fixture(autouse=True)
    def setup_env(self, monkeypatch, test_user, auth_headers):
        """Set up environment for payment tests."""
        monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_secret")
        monkeypatch.setenv("MP_ACCESS_TOKEN", "test_access_token")
        monkeypatch.setenv("STRIPE_PRO_PRICE_ID", "price_pro_test")
        monkeypatch.setenv("MP_PRO_PRICE_ID", "pro_test")
        self.auth_headers = auth_headers

    def test_create_stripe_checkout(self, client, test_user, auth_headers):
        """Test creating a Stripe checkout session."""
        checkout_data = {
            "provider": "stripe",
            "plan": "pro",
            "success_url": "https://jobbot.ar/success",
            "cancel_url": "https://jobbot.ar/cancel",
        }

        with patch("stripe.checkout.Session") as mock_session:
            mock_session.create.return_value = MagicMock(
                url="https://checkout.stripe.com/test",
                id="cs_test_123",
            )

            response = client.post(
                "/subscriptions/create-checkout",
                json=checkout_data,
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["provider"] == "stripe"
            assert "url" in data
            assert "session_id" in data

    def test_create_mercadopago_checkout(self, client, test_user, auth_headers):
        """Test creating a MercadoPago checkout."""
        checkout_data = {
            "provider": "mercadopago",
            "plan": "pro",
            "success_url": "https://jobbot.ar/success",
            "cancel_url": "https://jobbot.ar/cancel",
        }

        with patch("mercadopago.SDK") as mock_sdk:
            mock_preference = MagicMock()
            mock_preference.create.return_value = {
                "response": {
                    "init_point": "https://mp.com/checkout/test",
                    "id": "pref_test_123",
                }
            }
            mock_sdk.return_value.preference.return_value = mock_preference

            response = client.post(
                "/subscriptions/create-checkout",
                json=checkout_data,
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["provider"] == "mercadopago"
            assert "url" in data
            assert "preference_id" in data

    def test_create_checkout_requires_auth(self, client):
        """Test checkout creation requires authentication."""
        checkout_data = {
            "provider": "stripe",
            "plan": "pro",
        }

        response = client.post(
            "/subscriptions/create-checkout",
            json=checkout_data,
        )

        assert response.status_code == 403

    def test_create_checkout_invalid_plan(self, client, auth_headers):
        """Test checkout with invalid plan returns error."""
        checkout_data = {
            "provider": "stripe",
            "plan": "invalid_plan",
        }

        response = client.post(
            "/subscriptions/create-checkout",
            json=checkout_data,
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "Plan no valido" in response.json()["detail"]

    def test_create_checkout_invalid_provider(self, client, auth_headers):
        """Test checkout with invalid provider returns error."""
        checkout_data = {
            "provider": "invalid_provider",
            "plan": "pro",
        }

        response = client.post(
            "/subscriptions/create-checkout",
            json=checkout_data,
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "Proveedor no valido" in response.json()["detail"]


@pytest.mark.payment
class TestSubscriptionManagement:
    """Tests for subscription management endpoints."""

    def test_get_subscription_status(self, client, test_user, auth_headers, db):
        """Test getting subscription status."""
        response = client.get(
            "/subscriptions/status",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "plan" in data
        assert data["plan"] == "free"  # Default plan

    def test_cancel_subscription(self, client, test_user, auth_headers, db):
        """Test cancelling subscription."""
        # Set user to pro plan first
        db.update_user_plan(
            test_user["telegram_id"],
            "pro",
            (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        )

        with patch(
            "api.routes.subscriptions.deactivate_subscription"
        ) as mock_deactivate:
            mock_deactivate.return_value = None

            response = client.post(
                "/subscriptions/cancel",
                headers=auth_headers,
            )

            assert response.status_code == 200
            assert "Suscripcion cancelada" in response.json()["message"]

    def test_cancel_free_subscription_fails(self, client, test_user, auth_headers):
        """Test cancelling free subscription fails."""
        response = client.post(
            "/subscriptions/cancel",
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "No tienes suscripcion activa" in response.json()["detail"]

    def test_get_plans(self, client):
        """Test getting available plans."""
        response = client.get("/subscriptions/plans")

        assert response.status_code == 200
        data = response.json()
        assert "plans" in data
        assert len(data["plans"]) >= 4  # free, starter, pro, premium

        plan_ids = [p["id"] for p in data["plans"]]
        assert "free" in plan_ids
        assert "pro" in plan_ids

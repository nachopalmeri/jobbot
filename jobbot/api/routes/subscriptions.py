"""
Enhanced Subscriptions Routes with Circuit Breaker and DLQ
Production-ready payment processing with reliability patterns.
"""

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel

try:
    from job_bot.database import Database
except ImportError:
    from database import Database

from ..core import (
    stripe_circuit,
    telegram_circuit,
    retry,
    RetryConfig,
    dlq,
)
from .auth import get_authenticated_user, get_db


logger = logging.getLogger(__name__)
router = APIRouter()

PLANS = {
    "starter": {
        "price_usd": 3,
        "name": "Starter",
        "stripe_price_id": os.getenv("STRIPE_STARTER_PRICE_ID", "price_starter"),
        "mp_price_id": os.getenv("MP_STARTER_PRICE_ID", "starter"),
    },
    "pro": {
        "price_usd": 5,
        "name": "Pro",
        "stripe_price_id": os.getenv("STRIPE_PRO_PRICE_ID", "price_pro"),
        "mp_price_id": os.getenv("MP_PRO_PRICE_ID", "pro"),
    },
    "premium": {
        "price_usd": 15,
        "name": "Premium",
        "stripe_price_id": os.getenv("STRIPE_PREMIUM_PRICE_ID", "price_premium"),
        "mp_price_id": os.getenv("MP_PREMIUM_PRICE_ID", "premium"),
    },
}


class CheckoutRequest(BaseModel):
    provider: str
    plan: str
    success_url: str = "https://jobbot.ar/success"
    cancel_url: str = "https://jobbot.ar/cancel"


def _subscription_expiry_iso(days: int = 30) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def _request_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _validate_ip_whitelist(request: Request, env_key: str):
    """Validate request IP against whitelist."""
    raw = os.getenv(env_key, "").strip()
    if not raw:
        return
    allowed_ips = {item.strip() for item in raw.split(",") if item.strip()}
    if _request_ip(request) not in allowed_ips:
        raise HTTPException(status_code=403, detail="IP no autorizada")


def _validate_mp_request(request: Request):
    """Validate MercadoPago webhook request."""
    _validate_ip_whitelist(request, "MP_WEBHOOK_IPS")
    secret = os.getenv("MP_WEBHOOK_SECRET", "").strip()
    if not secret:
        return
    signature = request.headers.get("x-signature", "")
    if signature != secret:
        raise HTTPException(status_code=400, detail="Invalid signature")


def _validate_coinbase_request(body: bytes, signature: str):
    """Validate Coinbase webhook signature."""
    secret = os.getenv("COINBASE_WEBHOOK_SECRET", "").strip()
    if not secret:
        return
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")


@router.get("/plans")
async def get_plans():
    """Get available subscription plans."""
    return {
        "plans": [
            {
                "id": "free",
                "name": "Free",
                "price": 0,
                "currency": "USD",
                "features": [
                    "5 busquedas por dia",
                    "Hasta 5 resultados por consulta",
                    "Dashboard y pipeline basico",
                ],
            },
            {
                "id": "starter",
                "name": "Starter",
                "price": 3,
                "currency": "USD",
                "features": [
                    "30 busquedas por dia",
                    "Resultados completos",
                    "Pipeline de postulaciones",
                    "Alertas automatizadas por Telegram",
                ],
            },
            {
                "id": "pro",
                "name": "Pro",
                "price": 5,
                "currency": "USD",
                "features": [
                    "80 busquedas por dia",
                    "Resultados completos y filtros avanzados",
                    "Analisis de CV con IA",
                    "Pipeline de postulaciones",
                    "Alertas automatizadas por Telegram",
                ],
            },
            {
                "id": "premium",
                "name": "Premium",
                "price": 15,
                "currency": "USD",
                "features": [
                    "Todo de Pro",
                    "CV Tailoring",
                    "Entrevistas mock con IA",
                    "Busquedas ilimitadas",
                    "Mayor cuota diaria de IA",
                ],
            },
        ]
    }


@router.get("/status")
async def get_subscription_status(
    current_user: dict = Depends(get_authenticated_user),
    db: Database = Depends(get_db)
):
    """Get current user's subscription status."""
    web_user = db.get_web_user(current_user["telegram_id"]) or {}
    plan = db.get_user_plan(current_user["telegram_id"])
    return {
        "plan": plan,
        "status": web_user.get("subscription_status") or ("active" if plan != "free" else None),
        "expires_at": web_user.get("subscription_expires_at"),
    }


@router.post("/create-checkout")
async def create_checkout_session(
    checkout: CheckoutRequest,
    current_user: dict = Depends(get_authenticated_user),
    db: Database = Depends(get_db),
):
    """Create checkout session for subscription."""
    if checkout.plan not in PLANS:
        raise HTTPException(status_code=400, detail="Plan no valido")

    plan = PLANS[checkout.plan]
    web_user = db.get_web_user(current_user["telegram_id"]) or {}
    payer_email = web_user.get("email")
    payer = {**current_user, "email": payer_email}

    if checkout.provider == "stripe":
        return await create_stripe_checkout(checkout, payer, plan)
    if checkout.provider == "mercadopago":
        return await create_mercadopago_checkout(checkout, payer, plan)
    if checkout.provider == "crypto":
        return await create_crypto_checkout(checkout, current_user, plan)
    
    raise HTTPException(status_code=400, detail="Proveedor no valido")


@retry(
    max_retries=3,
    base_delay_seconds=1.0,
    retryable_exceptions=(Exception,)
)
async def create_stripe_checkout(checkout: CheckoutRequest, user: dict, plan: dict):
    """Create Stripe checkout session with retry logic and circuit breaker."""
    import stripe
    
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
    if not stripe.api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe no configurado",
        )
    
    def _create_session():
        session_payload = {
            "payment_method_types": ["card"],
            "line_items": [{"price": plan["stripe_price_id"], "quantity": 1}],
            "mode": "subscription",
            "success_url": checkout.success_url + "?session_id={CHECKOUT_SESSION_ID}",
            "cancel_url": checkout.cancel_url,
            "metadata": {"telegram_id": str(user["telegram_id"]), "plan": checkout.plan},
        }
        if user.get("email") and "@" in user["email"]:
            session_payload["customer_email"] = user["email"]
        
        return stripe.checkout.Session.create(**session_payload)
    
    try:
        # Use circuit breaker to protect against Stripe failures
        session = await stripe_circuit.call(_create_session)
        return {"provider": "stripe", "url": session.url, "session_id": session.id}
    except Exception as e:
        logger.error(f"Stripe checkout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment service temporarily unavailable",
        )


@retry(
    max_retries=2,
    base_delay_seconds=1.0,
    retryable_exceptions=(Exception,)
)
async def create_mercadopago_checkout(checkout: CheckoutRequest, user: dict, plan: dict):
    """Create MercadoPago checkout with retry logic."""
    import mercadopago
    
    access_token = os.getenv("MP_ACCESS_TOKEN", "")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MercadoPago no configurado",
        )
    
    sdk = mercadopago.SDK(access_token)
    preference_payload = {
        "items": [
            {
                "title": f"JobBot {plan['name']}",
                "quantity": 1,
                "unit_price": plan["price_usd"],
                "currency_id": "USD",
            }
        ],
        "metadata": {"telegram_id": str(user["telegram_id"]), "plan": checkout.plan},
        "back_urls": {
            "success": checkout.success_url,
            "failure": checkout.cancel_url,
            "pending": checkout.cancel_url,
        },
        "auto_return": "approved",
    }
    if user.get("email") and "@" in user["email"]:
        preference_payload["payer"] = {"email": user["email"]}
    
    try:
        preference = sdk.preference().create(preference_payload)
        return {
            "provider": "mercadopago",
            "url": preference["response"]["init_point"],
            "preference_id": preference["response"]["id"],
        }
    except Exception as e:
        logger.error(f"MercadoPago checkout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment service temporarily unavailable",
        )


async def create_crypto_checkout(checkout: CheckoutRequest, user: dict, plan: dict):
    """Create crypto checkout - currently unavailable."""
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Checkout crypto no disponible en este despliegue",
    )


@router.post("/webhook/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="stripe-signature"),
    db: Database = Depends(get_db),
):
    """Handle Stripe webhook with DLQ for failed processing."""
    import stripe
    
    body = await request.body()
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    
    if not webhook_secret:
        logger.error("Stripe webhook secret not configured")
        raise HTTPException(status_code=503, detail="Stripe webhook no configurado")
    
    try:
        event = stripe.Webhook.construct_event(body, stripe_signature, webhook_secret)
    except stripe.error.SignatureVerificationError:
        logger.warning("Invalid Stripe webhook signature")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except ValueError:
        logger.warning("Invalid Stripe webhook payload")
        raise HTTPException(status_code=400, detail="Invalid payload")
    
    # Check idempotency
    event_id = event.get("id")
    if event_id and db.is_webhook_processed(event_id):
        return {"status": "already_processed"}
    
    try:
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            metadata = session.get("metadata", {})
            await activate_subscription(
                db,
                metadata.get("telegram_id"),
                metadata.get("plan", "pro"),
                "stripe",
                session.get("subscription") or session.get("id"),
            )
        elif event["type"] == "customer.subscription.deleted":
            metadata = event["data"]["object"].get("metadata", {})
            await deactivate_subscription(db, metadata.get("telegram_id"))
        
        # Mark as processed
        if event_id:
            db.mark_webhook_processed(event_id, "stripe", event["type"])
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Stripe webhook processing error: {e}")
        
        # Add to DLQ for retry
        await dlq.enqueue(
            operation_type="stripe_webhook",
            payload={"event": event, "body": body.decode()},
            error=str(e),
            max_retries=5,
        )
        
        # Return 200 to prevent Stripe from retrying immediately
        # We'll handle retry via DLQ
        return {"status": "queued_for_retry", "error": str(e)}


@router.post("/webhook/mercadopago")
async def mercadopago_webhook(request: Request, db: Database = Depends(get_db)):
    """Handle MercadoPago webhook with validation."""
    _validate_mp_request(request)
    body = await request.json()
    
    if body.get("type") == "payment":
        payment = body.get("data", {}).get("resource", {})
        payment_id = str(payment.get("id", ""))
        
        # Check idempotency
        if payment_id and db.is_webhook_processed(payment_id):
            return {"status": "already_processed"}
        
        try:
            if payment.get("status") == "approved":
                metadata = payment.get("metadata", {})
                await activate_subscription(
                    db,
                    metadata.get("telegram_id"),
                    metadata.get("plan", "pro"),
                    "mercadopago",
                    payment_id,
                )
            
            # Mark as processed
            if payment_id:
                db.mark_webhook_processed(payment_id, "mercadopago", "payment.approved")
            
            return {"status": "success"}
            
        except Exception as e:
            logger.error(f"MercadoPago webhook processing error: {e}")
            
            await dlq.enqueue(
                operation_type="mp_webhook",
                payload=body,
                error=str(e),
            )
            
            return {"status": "queued_for_retry"}
    
    return {"status": "ignored"}


@router.post("/webhook/crypto")
async def crypto_webhook(
    request: Request,
    x_cc_webhook_signature: Optional[str] = Header(None),
    db: Database = Depends(get_db),
):
    """Handle Coinbase webhook."""
    body = await request.body()
    _validate_coinbase_request(body, x_cc_webhook_signature or "")
    
    payload = await request.json()
    event = payload.get("event", {})
    event_id = event.get("id")
    
    # Check idempotency
    if event_id and db.is_webhook_processed(event_id):
        return {"status": "already_processed"}
    
    try:
        if event.get("type") == "charge:confirmed":
            charge = event.get("data", {})
            metadata = charge.get("metadata", {})
            await activate_subscription(
                db,
                metadata.get("telegram_id"),
                metadata.get("plan", "pro"),
                "crypto",
                charge.get("id"),
            )
        
        # Mark as processed
        if event_id:
            db.mark_webhook_processed(event_id, "crypto", "charge:confirmed")
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Crypto webhook processing error: {e}")
        
        await dlq.enqueue(
            operation_type="crypto_webhook",
            payload=payload,
            error=str(e),
        )
        
        return {"status": "queued_for_retry"}


@retry(
    max_retries=3,
    base_delay_seconds=0.5,
    retryable_exceptions=(Exception,)
)
async def _send_telegram_notification(telegram_id: int, message: str) -> bool:
    """Send Telegram notification with retry and circuit breaker."""
    try:
        import aiohttp
        
        token = os.getenv("TELEGRAM_TOKEN")
        if not token:
            logger.warning("TELEGRAM_TOKEN not configured, skipping notification")
            return False
        
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": telegram_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        
        async def _send():
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        return True
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")
        
        return await telegram_circuit.call(_send)
        
    except Exception as e:
        logger.error(f"Error sending Telegram notification to {telegram_id}: {e}")
        return False


async def _notify_plan_change(telegram_id: int, plan: str, expiry: str) -> bool:
    """Notify user about subscription plan change."""
    plan_names = {
        "starter": "Starter ($3/mes)",
        "pro": "Pro ($5/mes)",
        "premium": "Premium ($15/mes)",
        "free": "Free"
    }
    plan_name = plan_names.get(plan, plan)
    
    # Parse expiry date for display
    try:
        expiry_date = datetime.fromisoformat(expiry)
        expiry_formatted = expiry_date.strftime("%d/%m/%Y")
    except:
        expiry_formatted = expiry[:10] if expiry else "30 dias"
    
    message = (
        "✅ <b>¡Suscripcion Activada!</b>\n\n"
        f"Tu plan <b>{plan_name}</b> esta ahora activo.\n\n"
        f"📅 Valido hasta: <b>{expiry_formatted}</b>\n\n"
        "🚀 Ahora tienes acceso a todas las funciones premium:\n"
        "• Busquedas ilimitadas\n"
        "• Alertas automaticas cada hora\n"
        "• Analisis de CV con IA\n"
        "• Simulador de entrevistas\n"
        "• Empresas preferidas\n\n"
        "¡Gracias por confiar en JobBot! 🎯"
    )
    
    return await _send_telegram_notification(telegram_id, message)


async def activate_subscription(
    db: Database, telegram_id: str, plan: str, provider: str, payment_id: str
):
    """Activate user subscription and notify."""
    if not telegram_id:
        raise ValueError("telegram_id requerido")
    
    telegram_id = int(telegram_id)
    expiry = _subscription_expiry_iso()
    
    db.update_user_plan(telegram_id, plan, expiry)
    db.record_payment(
        telegram_id=telegram_id,
        provider=provider,
        amount=PLANS.get(plan, {}).get("price_usd", 0),
        currency="USD",
        status="paid",
        provider_payment_id=payment_id,
    )
    
    # Notify user
    await _notify_plan_change(telegram_id, plan, expiry)


async def _notify_cancellation(telegram_id: int) -> bool:
    """Notify user about subscription cancellation."""
    message = (
        "📋 <b>Suscripcion Cancelada</b>\n\n"
        "Tu suscripcion ha sido cancelada y volviste al plan <b>Free</b>.\n\n"
        "🔄 Ahora tenes:\n"
        "• 5 busquedas por dia\n"
        "• Alertas cada 6 horas\n"
        "• Acceso al dashboard\n\n"
        "💡 ¿Queres volver a Pro? Escribi /precios en el bot."
    )
    
    return await _send_telegram_notification(telegram_id, message)


async def deactivate_subscription(db: Database, telegram_id: str, notify: bool = True):
    """Deactivate subscription and notify."""
    if not telegram_id:
        return
    
    tid = int(telegram_id)
    db.update_user_plan(tid, "free")
    
    if notify:
        await _notify_cancellation(tid)


@router.post("/cancel")
async def cancel_subscription(
    current_user: dict = Depends(get_authenticated_user),
    db: Database = Depends(get_db)
):
    """Cancel user subscription."""
    if current_user["plan"] == "free":
        raise HTTPException(status_code=400, detail="No tienes suscripcion activa")
    
    await deactivate_subscription(db, str(current_user["telegram_id"]), notify=True)
    return {"message": "Suscripcion cancelada", "plan": "free", "expires_at": None}


@router.post("/upgrade")
async def upgrade_plan(
    plan: str,
    current_user: dict = Depends(get_authenticated_user)
):
    """Initiate plan upgrade."""
    if plan not in PLANS:
        raise HTTPException(status_code=400, detail="Plan no valido")
    
    return {
        "message": f"Actualizando a plan {PLANS[plan]['name']}",
        "current_plan": current_user["plan"],
        "new_plan": plan,
        "price": PLANS[plan]["price_usd"],
    }

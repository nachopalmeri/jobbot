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

from .auth import get_authenticated_user, get_db


logger = logging.getLogger(__name__)
router = APIRouter()

PLANS = {
    "starter": {
        "price_usd": 4,
        "yearly_price_usd": 40,
        "name": "Starter",
        "stripe_price_id": os.getenv("STRIPE_STARTER_PRICE_ID", "price_starter"),
        "stripe_yearly_price_id": os.getenv("STRIPE_STARTER_YEARLY_PRICE_ID", ""),
        "mp_price_id": os.getenv("MP_STARTER_PRICE_ID", "starter"),
        "mp_yearly_price_id": os.getenv("MP_STARTER_YEARLY_PRICE_ID", ""),
    },
    "pro": {
        "price_usd": 8,
        "yearly_price_usd": 80,
        "name": "Pro",
        "stripe_price_id": os.getenv("STRIPE_PRO_PRICE_ID", "price_pro"),
        "stripe_yearly_price_id": os.getenv("STRIPE_PRO_YEARLY_PRICE_ID", ""),
        "mp_price_id": os.getenv("MP_PRO_PRICE_ID", "pro"),
        "mp_yearly_price_id": os.getenv("MP_PRO_YEARLY_PRICE_ID", ""),
    },
    "premium": {
        "price_usd": 12,
        "yearly_price_usd": 120,
        "name": "Premium",
        "stripe_price_id": os.getenv("STRIPE_PREMIUM_PRICE_ID", "price_premium"),
        "stripe_yearly_price_id": os.getenv("STRIPE_PREMIUM_YEARLY_PRICE_ID", ""),
        "mp_price_id": os.getenv("MP_PREMIUM_PRICE_ID", "premium"),
        "mp_yearly_price_id": os.getenv("MP_PREMIUM_YEARLY_PRICE_ID", ""),
    },
}


class CheckoutRequest(BaseModel):
    provider: str
    plan: str
    billing_cycle: str = "monthly"
    success_url: str = "https://app-jobbot.vercel.app/dashboard/suscripcion"
    cancel_url: str = "https://app-jobbot.vercel.app/dashboard/suscripcion"


def _subscription_expiry_iso(days: int = 30) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def _validate_billing_cycle(billing_cycle: str) -> str:
    normalized = (billing_cycle or "monthly").strip().lower()
    if normalized not in {"monthly", "yearly"}:
        raise HTTPException(status_code=400, detail="Ciclo de facturacion no valido")
    return normalized


def _plan_price(plan: dict, billing_cycle: str) -> float:
    return plan["yearly_price_usd"] if billing_cycle == "yearly" else plan["price_usd"]


def _stripe_price_id(plan: dict, billing_cycle: str) -> str:
    if billing_cycle == "yearly":
        yearly_price_id = (plan.get("stripe_yearly_price_id") or "").strip()
        if not yearly_price_id:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Stripe anual no configurado todavia",
            )
        return yearly_price_id
    monthly_price_id = (plan.get("stripe_price_id") or "").strip()
    if not monthly_price_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe mensual no configurado todavia",
        )
    return monthly_price_id


def _mp_price_id(plan: dict, billing_cycle: str) -> str:
    if billing_cycle == "yearly":
        yearly_price_id = (plan.get("mp_yearly_price_id") or "").strip()
        if yearly_price_id:
            return yearly_price_id
    return plan["mp_price_id"]


def _request_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _validate_ip_whitelist(request: Request, env_key: str):
    raw = os.getenv(env_key, "").strip()
    if not raw:
        return
    allowed_ips = {item.strip() for item in raw.split(",") if item.strip()}
    if _request_ip(request) not in allowed_ips:
        raise HTTPException(status_code=403, detail="IP no autorizada")


def _validate_mp_request(request: Request):
    _validate_ip_whitelist(request, "MP_WEBHOOK_IPS")
    secret = os.getenv("MP_WEBHOOK_SECRET", "").strip()
    if not secret:
        return
    signature = request.headers.get("x-signature", "")
    if signature != secret:
        raise HTTPException(status_code=400, detail="Invalid signature")


def _validate_coinbase_request(body: bytes, signature: str):
    secret = os.getenv("COINBASE_WEBHOOK_SECRET", "").strip()
    if not secret:
        return
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")


@router.get("/plans")
async def get_plans():
    return {
        "plans": [
            {
                "id": "free",
                "name": "Free",
                "price": 0,
                "currency": "USD",
                "features": [
                    "3 busquedas guiadas por dia",
                    "Hasta 3 resultados visibles por consulta",
                    "Dashboard liviano",
                    "Score ATS inicial de CV",
                ],
            },
            {
                "id": "starter",
                "name": "Starter",
                "price": 4,
                "monthly_price": 4,
                "yearly_price": 40,
                "yearly_monthly_equivalent": 3.33,
                "yearly_savings_percent": 17,
                "currency": "USD",
                "features": [
                    "12 busquedas por dia",
                    "Resultados completos",
                    "Pipeline de postulaciones",
                    "Alertas automatizadas por Telegram",
                    "CV score y quick wins",
                ],
            },
            {
                "id": "pro",
                "name": "Pro",
                "price": 8,
                "monthly_price": 8,
                "yearly_price": 80,
                "yearly_monthly_equivalent": 6.67,
                "yearly_savings_percent": 17,
                "currency": "USD",
                "features": [
                    "40 busquedas por dia",
                    "Resultados completos y filtros avanzados",
                    "4 analisis de CV con IA por mes",
                    "Match score y keywords faltantes",
                    "Pipeline de postulaciones",
                    "Alertas automatizadas por Telegram",
                    "Feedback recruiter para vacantes clave",
                ],
            },
            {
                "id": "premium",
                "name": "Premium",
                "price": 12,
                "monthly_price": 12,
                "yearly_price": 120,
                "yearly_monthly_equivalent": 10,
                "yearly_savings_percent": 17,
                "currency": "USD",
                "features": [
                    "Todo de Pro",
                    "CV Intelligence Suite destacada",
                    "CV Tailoring y cover letters",
                    "Entrevistas mock con IA",
                    "120 busquedas por dia",
                    "20 analisis IA + 10 mock interviews por mes",
                    "Workflow completo para aplicar mejor",
                ],
            },
        ]
    }


@router.get("/status")
async def get_subscription_status(
    current_user: dict = Depends(get_authenticated_user), db: Database = Depends(get_db)
):
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
    if checkout.plan not in PLANS:
        raise HTTPException(status_code=400, detail="Plan no valido")
    billing_cycle = _validate_billing_cycle(checkout.billing_cycle)

    plan = PLANS[checkout.plan]
    web_user = db.get_web_user(current_user["telegram_id"]) or {}
    payer_email = web_user.get("email")
    payer = {**current_user, "email": payer_email}

    if checkout.provider == "stripe":
        return await create_stripe_checkout(checkout, payer, plan, billing_cycle)
    if checkout.provider == "mercadopago":
        return await create_mercadopago_checkout(checkout, payer, plan, billing_cycle)
    if checkout.provider == "crypto":
        return await create_crypto_checkout(checkout, current_user, plan, billing_cycle)
    raise HTTPException(status_code=400, detail="Proveedor no valido")


async def create_stripe_checkout(
    checkout: CheckoutRequest, user: dict, plan: dict, billing_cycle: str
):
    import stripe

    stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
    if not stripe.api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe no configurado",
        )

    metadata = {
        "telegram_id": str(user["telegram_id"]),
        "plan": checkout.plan,
        "billing_cycle": billing_cycle,
    }
    session_payload = {
        "payment_method_types": ["card"],
        "line_items": [{"price": _stripe_price_id(plan, billing_cycle), "quantity": 1}],
        "mode": "subscription",
        "success_url": checkout.success_url + "?session_id={CHECKOUT_SESSION_ID}",
        "cancel_url": checkout.cancel_url,
        "metadata": metadata,
        "subscription_data": {"metadata": metadata},
    }
    if user.get("email") and "@" in user["email"]:
        session_payload["customer_email"] = user["email"]

    session = stripe.checkout.Session.create(**session_payload)
    return {
        "provider": "stripe",
        "url": session.url,
        "session_id": session.id,
        "billing_cycle": billing_cycle,
    }


async def create_mercadopago_checkout(
    checkout: CheckoutRequest, user: dict, plan: dict, billing_cycle: str
):
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
                "title": f"JobBot {plan['name']} ({'anual' if billing_cycle == 'yearly' else 'mensual'})",
                "quantity": 1,
                "unit_price": _plan_price(plan, billing_cycle),
                "currency_id": "USD",
            }
        ],
        "metadata": {
            "telegram_id": str(user["telegram_id"]),
            "plan": checkout.plan,
            "billing_cycle": billing_cycle,
            "mp_plan_price_id": _mp_price_id(plan, billing_cycle),
        },
        "back_urls": {
            "success": checkout.success_url,
            "failure": checkout.cancel_url,
            "pending": checkout.cancel_url,
        },
        "auto_return": "approved",
    }
    if user.get("email") and "@" in user["email"]:
        preference_payload["payer"] = {"email": user["email"]}

    preference = sdk.preference().create(preference_payload)
    return {
        "provider": "mercadopago",
        "url": preference["response"]["init_point"],
        "preference_id": preference["response"]["id"],
        "billing_cycle": billing_cycle,
    }


async def create_crypto_checkout(
    checkout: CheckoutRequest, user: dict, plan: dict, billing_cycle: str
):
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
    import stripe

    body = await request.body()
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    if not webhook_secret:
        raise HTTPException(status_code=503, detail="Stripe webhook no configurado")

    try:
        event = stripe.Webhook.construct_event(body, stripe_signature, webhook_secret)
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")

    # Verificar idempotencia
    event_id = event.get("id")
    if event_id and db.is_webhook_processed(event_id):
        return {"status": "already_processed"}

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session.get("metadata", {})
        await activate_subscription(
            db,
            metadata.get("telegram_id"),
            metadata.get("plan", "pro"),
            metadata.get("billing_cycle", "monthly"),
            "stripe",
            session.get("subscription") or session.get("id"),
        )
    elif event["type"] == "customer.subscription.deleted":
        metadata = event["data"]["object"].get("metadata", {})
        await deactivate_subscription(db, metadata.get("telegram_id"))

    # Marcar como procesado
    if event_id:
        db.mark_webhook_processed(event_id, "stripe", event["type"])

    return {"status": "success"}


@router.post("/webhook/mercadopago")
async def mercadopago_webhook(request: Request, db: Database = Depends(get_db)):
    _validate_mp_request(request)
    body = await request.json()

    if body.get("type") == "payment":
        payment = body.get("data", {}).get("resource", {})
        payment_id = str(payment.get("id", ""))
        
        # Verificar idempotencia
        if payment_id and db.is_webhook_processed(payment_id):
            return {"status": "already_processed"}
        
        if payment.get("status") == "approved":
            metadata = payment.get("metadata", {})
            await activate_subscription(
                db,
                metadata.get("telegram_id"),
                metadata.get("plan", "pro"),
                metadata.get("billing_cycle", "monthly"),
                "mercadopago",
                payment_id,
            )
            
            # Marcar como procesado
            if payment_id:
                db.mark_webhook_processed(payment_id, "mercadopago", "payment.approved")

    return {"status": "success"}


@router.post("/webhook/crypto")
async def crypto_webhook(
    request: Request,
    x_cc_webhook_signature: Optional[str] = Header(None),
    db: Database = Depends(get_db),
):
    body = await request.body()
    _validate_coinbase_request(body, x_cc_webhook_signature or "")
    payload = await request.json()
    
    event = payload.get("event", {})
    event_id = event.get("id")
    
    # Verificar idempotencia
    if event_id and db.is_webhook_processed(event_id):
        return {"status": "already_processed"}

    if event.get("type") == "charge:confirmed":
        charge = event.get("data", {})
        metadata = charge.get("metadata", {})
        await activate_subscription(
            db,
            metadata.get("telegram_id"),
            metadata.get("plan", "pro"),
            metadata.get("billing_cycle", "monthly"),
            "crypto",
            charge.get("id"),
        )
        
        # Marcar como procesado
        if event_id:
            db.mark_webhook_processed(event_id, "crypto", "charge:confirmed")

    return {"status": "success"}


async def _send_telegram_notification(telegram_id: int, message: str) -> bool:
    """Send a Telegram notification to a user."""
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
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    logger.info("Notification sent to user %s", telegram_id)
                    return True
                else:
                    error_text = await response.text()
                    logger.error("Failed to send notification to %s: %s", telegram_id, error_text)
                    return False
    except Exception as e:
        logger.error("Error sending Telegram notification to %s: %s", telegram_id, e)
        return False


async def _notify_plan_change(
    telegram_id: int, plan: str, expiry: str, billing_cycle: str = "monthly"
) -> bool:
    """Notify user about subscription plan change."""
    plan_names = {
        "starter": "Starter",
        "pro": "Pro",
        "premium": "Premium",
        "free": "Free"
    }
    billing_labels = {
        "monthly": "mensual",
        "yearly": "anual",
    }
    plan_name = plan_names.get(plan, plan)
    plan_price = _plan_price(PLANS.get(plan, {"price_usd": 0, "yearly_price_usd": 0}), billing_cycle)
    plan_label = f"{plan_name} (${plan_price}/{ 'año' if billing_cycle == 'yearly' else 'mes'})"
    
    # Parse expiry date for display
    try:
        expiry_date = datetime.fromisoformat(expiry)
        expiry_formatted = expiry_date.strftime("%d/%m/%Y")
    except:
        expiry_formatted = expiry[:10] if expiry else "30 días"
    
    message = (
        "✅ <b>¡Suscripción Activada!</b>\n\n"
        f"Tu plan <b>{plan_label}</b> en modalidad <b>{billing_labels.get(billing_cycle, billing_cycle)}</b> está ahora activo.\n\n"
        f"📅 Válido hasta: <b>{expiry_formatted}</b>\n\n"
        "🚀 Ahora tenés acceso a un flujo mucho más fuerte:\n"
        "• Más búsquedas y resultados completos\n"
        "• Tracker y alertas automáticas\n"
        "• CV Intelligence dentro del dashboard\n"
        "• Match, cover letters o mock interviews según tu plan\n\n"
        "¡Gracias por confiar en JobBot! 🎯"
    )
    
    return await _send_telegram_notification(telegram_id, message)


async def activate_subscription(
    db: Database, telegram_id: str, plan: str, billing_cycle: str, provider: str, payment_id: str
):
    if not telegram_id:
        raise ValueError("telegram_id requerido")

    telegram_id = int(telegram_id)
    normalized_cycle = _validate_billing_cycle(billing_cycle)
    expiry = _subscription_expiry_iso(365 if normalized_cycle == "yearly" else 30)
    db.update_user_plan(telegram_id, plan, expiry)
    db.record_payment(
        telegram_id=telegram_id,
        provider=provider,
        amount=_plan_price(PLANS.get(plan, {"price_usd": 0, "yearly_price_usd": 0}), normalized_cycle),
        currency="USD",
        status="paid",
        provider_payment_id=payment_id,
    )
    
    # Notify user about subscription activation
    await _notify_plan_change(telegram_id, plan, expiry, normalized_cycle)


async def _notify_cancellation(telegram_id: int) -> bool:
    """Notify user about subscription cancellation."""
    message = (
        "📋 <b>Suscripción Cancelada</b>\n\n"
        "Tu suscripción ha sido cancelada y volviste al plan <b>Free</b>.\n\n"
        "🔄 Ahora tenés:\n"
        "• 3 búsquedas guiadas por día\n"
        "• ATS básico de CV\n"
        "• Acceso al dashboard liviano\n\n"
        "💡 ¿Querés volver a Pro? Escribí /precios en el bot."
    )
    
    return await _send_telegram_notification(telegram_id, message)


async def deactivate_subscription(db: Database, telegram_id: str, notify: bool = True):
    if not telegram_id:
        return
    
    tid = int(telegram_id)
    db.update_user_plan(tid, "free")
    
    if notify:
        await _notify_cancellation(tid)


@router.post("/cancel")
async def cancel_subscription(
    current_user: dict = Depends(get_authenticated_user), db: Database = Depends(get_db)
):
    if current_user["plan"] == "free":
        raise HTTPException(status_code=400, detail="No tienes suscripcion activa")

    await deactivate_subscription(db, str(current_user["telegram_id"]), notify=True)
    return {"message": "Suscripcion cancelada", "plan": "free", "expires_at": None}


@router.post("/upgrade")
async def upgrade_plan(plan: str, current_user: dict = Depends(get_authenticated_user)):
    if plan not in PLANS:
        raise HTTPException(status_code=400, detail="Plan no valido")

    return {
        "message": f"Actualizando a plan {PLANS[plan]['name']}",
        "current_plan": current_user["plan"],
        "new_plan": plan,
        "price": PLANS[plan]["price_usd"],
    }

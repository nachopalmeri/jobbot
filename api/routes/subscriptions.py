from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
import httpx
from pydantic import BaseModel

try:
    from job_bot.database import Database
except ImportError:
    from database import Database

from .auth import get_authenticated_user, get_db


logger = logging.getLogger(__name__)
router = APIRouter()
SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "support@jobbot.ar")
PUBLIC_APP_URL = os.getenv(
    "PUBLIC_APP_URL", os.getenv("DASHBOARD_URL", "https://app-jobbot.vercel.app")
).rstrip("/")
PUBLIC_API_URL = os.getenv("PUBLIC_API_URL", "").rstrip("/")


def _env(name: str) -> str:
    return os.getenv(name, "").strip()

PLANS = {
    "starter": {
        "price_usd": 4,
        "yearly_price_usd": 40,
        "name": "Starter",
        "stripe_price_id": _env("STRIPE_STARTER_PRICE_ID"),
        "stripe_yearly_price_id": _env("STRIPE_STARTER_YEARLY_PRICE_ID"),
        "mp_price_id": os.getenv("MP_STARTER_PRICE_ID", "starter"),
        "mp_yearly_price_id": os.getenv("MP_STARTER_YEARLY_PRICE_ID", ""),
    },
    "pro": {
        "price_usd": 8,
        "yearly_price_usd": 80,
        "name": "Pro",
        "stripe_price_id": _env("STRIPE_PRO_PRICE_ID"),
        "stripe_yearly_price_id": _env("STRIPE_PRO_YEARLY_PRICE_ID"),
        "mp_price_id": os.getenv("MP_PRO_PRICE_ID", "pro"),
        "mp_yearly_price_id": os.getenv("MP_PRO_YEARLY_PRICE_ID", ""),
    },
    "premium": {
        "price_usd": 12,
        "yearly_price_usd": 120,
        "name": "Premium",
        "stripe_price_id": _env("STRIPE_PREMIUM_PRICE_ID"),
        "stripe_yearly_price_id": _env("STRIPE_PREMIUM_YEARLY_PRICE_ID"),
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


def _billing_return_url() -> str:
    return f"{PUBLIC_APP_URL}/dashboard/suscripcion"


def _mp_external_reference(telegram_id: int, plan: str, billing_cycle: str) -> str:
    return f"{telegram_id}|{plan}|{billing_cycle}"


def _parse_mp_external_reference(external_reference: str) -> tuple[Optional[str], str, str]:
    parts = (external_reference or "").split("|")
    if len(parts) != 3:
        return None, "pro", "monthly"
    telegram_id, plan, billing_cycle = parts
    return telegram_id, plan or "pro", billing_cycle or "monthly"


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


def _extract_mp_signature_part(header_value: str, key: str) -> str:
    for part in (header_value or "").split(","):
        if "=" not in part:
            continue
        part_key, part_value = part.split("=", 1)
        if part_key.strip() == key:
            return part_value.strip()
    return ""


def _resolve_mp_data_id(payload: dict, request: Request) -> str:
    data = payload.get("data") or {}
    if isinstance(data, dict) and data.get("id") is not None:
        return str(data.get("id"))
    data_id = request.query_params.get("data.id") or request.query_params.get("id")
    return str(data_id or "")


def _validate_mp_request(request: Request, payload: Optional[dict] = None):
    _validate_ip_whitelist(request, "MP_WEBHOOK_IPS")
    secret = os.getenv("MP_WEBHOOK_SECRET", "").strip()
    if not secret:
        return

    signature = request.headers.get("x-signature", "")
    request_id = request.headers.get("x-request-id", "")
    ts = _extract_mp_signature_part(signature, "ts")
    received_hash = _extract_mp_signature_part(signature, "v1")
    data_id = _resolve_mp_data_id(payload or {}, request)

    if not signature or not request_id or not ts or not received_hash or not data_id:
        raise HTTPException(status_code=400, detail="Invalid signature")

    manifest = f"id:{data_id};request-id:{request_id};ts:{ts};"
    expected_hash = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_hash, received_hash):
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
        "provider": web_user.get("subscription_provider"),
        "billing_cycle": web_user.get("subscription_billing_cycle") or "monthly",
        "expires_at": web_user.get("subscription_expires_at"),
        "can_cancel": plan != "free",
        "can_manage_billing": web_user.get("subscription_provider") == "stripe"
        and bool(web_user.get("subscription_id")),
        "support_email": SUPPORT_EMAIL,
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
    access_token = os.getenv("MP_ACCESS_TOKEN", "")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MercadoPago no configurado",
        )

    frequency = 12 if billing_cycle == "yearly" else 1
    preapproval_payload = {
        "reason": f"JobBot {plan['name']} ({'anual' if billing_cycle == 'yearly' else 'mensual'})",
        "external_reference": _mp_external_reference(
            int(user["telegram_id"]), checkout.plan, billing_cycle
        ),
        "back_url": checkout.success_url,
        "status": "authorized",
        "auto_recurring": {
            "frequency": frequency,
            "frequency_type": "months",
            "transaction_amount": _plan_price(plan, billing_cycle),
            "currency_id": "USD",
        },
    }
    if PUBLIC_API_URL:
        preapproval_payload["notification_url"] = (
            f"{PUBLIC_API_URL}/subscriptions/webhook/mercadopago"
        )
    if user.get("email") and "@" in user["email"]:
        preapproval_payload["payer_email"] = user["email"]

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                "https://api.mercadopago.com/preapproval",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json=preapproval_payload,
            )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No se pudo iniciar MercadoPago",
        ) from exc
    if response.status_code >= 400:
        logger.error("[MP] Error creando preapproval: %s", response.text)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No se pudo iniciar MercadoPago",
        )

    preference = response.json()
    checkout_url = preference.get("init_point") or preference.get("sandbox_init_point")
    if not checkout_url:
        logger.error("[MP] Respuesta sin init_point: %s", preference)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="MercadoPago no devolvió un checkout válido",
        )

    return {
        "provider": "mercadopago",
        "url": checkout_url,
        "preference_id": preference.get("id"),
        "billing_cycle": billing_cycle,
    }


async def create_crypto_checkout(
    checkout: CheckoutRequest, user: dict, plan: dict, billing_cycle: str
):
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Checkout crypto no disponible en este despliegue",
    )


def _mercadopago_access_token() -> str:
    access_token = os.getenv("MP_ACCESS_TOKEN", "").strip()
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MercadoPago no configurado",
        )
    return access_token


async def _fetch_mercadopago_resource(path: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                f"https://api.mercadopago.com{path}",
                headers={"Authorization": f"Bearer {_mercadopago_access_token()}"},
            )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No se pudo validar la suscripción de MercadoPago",
        ) from exc

    if response.status_code >= 400:
        logger.error("[MP] Error consultando %s: %s", path, response.text)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No se pudo validar la suscripción de MercadoPago",
        )
    return response.json()


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
            subscription_id=session.get("subscription") or session.get("id"),
        )
    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        metadata = subscription.get("metadata", {})
        telegram_id = metadata.get("telegram_id")
        if not telegram_id:
            linked_user = db.get_web_user_by_subscription_id(subscription.get("id"))
            telegram_id = linked_user.get("telegram_id") if linked_user else None
        await deactivate_subscription(db, telegram_id, clear_metadata=True)

    # Marcar como procesado
    if event_id:
        db.mark_webhook_processed(event_id, "stripe", event["type"])

    return {"status": "success"}


@router.post("/webhook/mercadopago")
async def mercadopago_webhook(request: Request, db: Database = Depends(get_db)):
    try:
        body = await request.json()
    except Exception:
        body = {}
    _validate_mp_request(request, body)

    event_type = (
        body.get("type")
        or body.get("topic")
        or request.query_params.get("type")
        or request.query_params.get("topic")
        or ""
    )
    data = body.get("data") or {}
    resource_id = (
        data.get("id")
        or (data.get("resource") or {}).get("id")
        or request.query_params.get("data.id")
        or request.query_params.get("id")
        or ""
    )

    if event_type == "preapproval" and resource_id:
        preapproval = await _fetch_mercadopago_resource(f"/preapproval/{resource_id}")
        preapproval_id = str(preapproval.get("id", ""))
        event_key = f"mp:preapproval:{preapproval_id}:{preapproval.get('status', '')}"
        if preapproval_id and db.is_webhook_processed(event_key):
            return {"status": "already_processed"}

        telegram_id, plan, billing_cycle = _parse_mp_external_reference(
            preapproval.get("external_reference", "")
        )
        if preapproval.get("status") in {"authorized", "pending"} and telegram_id:
            await activate_subscription(
                db,
                telegram_id,
                plan,
                billing_cycle,
                "mercadopago",
                preapproval_id,
                subscription_id=preapproval_id,
            )
        elif preapproval.get("status") in {"cancelled", "paused"}:
            linked_user = db.get_web_user_by_subscription_id(preapproval_id)
            if linked_user:
                await deactivate_subscription(
                    db,
                    str(linked_user["telegram_id"]),
                    notify=False,
                    clear_metadata=True,
                )

        if preapproval_id:
            db.mark_webhook_processed(event_key, "mercadopago", f"preapproval.{preapproval.get('status')}")

    elif event_type == "payment" and resource_id:
        payment = await _fetch_mercadopago_resource(f"/v1/payments/{resource_id}")
        payment_id = str(payment.get("id", ""))
        event_key = f"mp:payment:{payment_id}:{payment.get('status', '')}"
        if payment_id and db.is_webhook_processed(event_key):
            return {"status": "already_processed"}

        if payment.get("status") == "approved":
            metadata = payment.get("metadata", {}) or {}
            await activate_subscription(
                db,
                metadata.get("telegram_id"),
                metadata.get("plan", "pro"),
                metadata.get("billing_cycle", "monthly"),
                "mercadopago",
                payment_id,
                subscription_id=metadata.get("subscription_id") or payment_id,
            )
        if payment_id:
            db.mark_webhook_processed(event_key, "mercadopago", f"payment.{payment.get('status')}")

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
    db: Database,
    telegram_id: str,
    plan: str,
    billing_cycle: str,
    provider: str,
    payment_id: str,
    subscription_id: Optional[str] = None,
):
    if not telegram_id:
        raise ValueError("telegram_id requerido")

    telegram_id = int(telegram_id)
    normalized_cycle = _validate_billing_cycle(billing_cycle)
    expiry = _subscription_expiry_iso(365 if normalized_cycle == "yearly" else 30)
    db.update_user_plan(telegram_id, plan, expiry)
    db.set_subscription_metadata(
        telegram_id,
        provider,
        subscription_id or payment_id,
        normalized_cycle,
        status="active",
        expires_at=expiry,
    )
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


async def _notify_cancel_at_period_end(telegram_id: int, expiry: Optional[str]) -> bool:
    expiry_label = expiry[:10] if expiry else "fin del ciclo actual"
    message = (
        "📋 <b>Cancelación programada</b>\n\n"
        "Tu suscripción no se va a renovar y se cancelará al final del período actual.\n\n"
        f"🗓️ Vas a mantener acceso hasta <b>{expiry_label}</b>.\n\n"
        f"Si necesitás ayuda, escribinos a <b>{SUPPORT_EMAIL}</b>."
    )
    return await _send_telegram_notification(telegram_id, message)


def _cancel_stripe_subscription(subscription_id: str) -> Optional[str]:
    import stripe

    stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "").strip()
    if not stripe.api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe no configurado",
        )

    subscription = stripe.Subscription.modify(
        subscription_id,
        cancel_at_period_end=True,
    )
    current_period_end = subscription.get("current_period_end")
    if not current_period_end:
        return None
    return datetime.fromtimestamp(current_period_end, timezone.utc).isoformat()


def _create_stripe_billing_portal(subscription_id: str) -> str:
    import stripe

    stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "").strip()
    if not stripe.api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe no configurado",
        )

    subscription = stripe.Subscription.retrieve(subscription_id)
    customer_id = subscription.get("customer")
    if not customer_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No pudimos encontrar el customer de Stripe para esta cuenta",
        )

    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=_billing_return_url(),
    )
    return session.url


async def _cancel_mercadopago_subscription(subscription_id: str):
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.put(
                f"https://api.mercadopago.com/preapproval/{subscription_id}",
                headers={
                    "Authorization": f"Bearer {_mercadopago_access_token()}",
                    "Content-Type": "application/json",
                },
                json={"status": "cancelled"},
            )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No pudimos cancelar MercadoPago en este momento",
        ) from exc

    if response.status_code >= 400:
        logger.error("[MP] Error cancelando preapproval %s: %s", subscription_id, response.text)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No pudimos cancelar MercadoPago en este momento",
        )


async def deactivate_subscription(
    db: Database, telegram_id: str, notify: bool = True, clear_metadata: bool = False
):
    if not telegram_id:
        return
    
    tid = int(telegram_id)
    db.update_user_plan(tid, "free")
    if clear_metadata:
        db.clear_subscription_metadata(tid)
    
    if notify:
        await _notify_cancellation(tid)


@router.post("/cancel")
async def cancel_subscription(
    current_user: dict = Depends(get_authenticated_user), db: Database = Depends(get_db)
):
    if current_user["plan"] == "free":
        raise HTTPException(status_code=400, detail="No tienes suscripcion activa")
    web_user = db.get_web_user(current_user["telegram_id"]) or {}
    provider = web_user.get("subscription_provider")
    subscription_id = web_user.get("subscription_id")
    billing_cycle = web_user.get("subscription_billing_cycle") or "monthly"
    expires_at = web_user.get("subscription_expires_at")

    if provider == "stripe" and subscription_id:
        expires_at = _cancel_stripe_subscription(subscription_id) or expires_at
        db.set_subscription_metadata(
            current_user["telegram_id"],
            provider,
            subscription_id,
            billing_cycle,
            status="cancel_at_period_end",
            expires_at=expires_at,
        )
        await _notify_cancel_at_period_end(current_user["telegram_id"], expires_at)
        return {
            "message": "La cancelacion quedó programada al final del período actual",
            "plan": current_user["plan"],
            "status": "cancel_at_period_end",
            "expires_at": expires_at,
        }

    if provider == "mercadopago" and subscription_id:
        await _cancel_mercadopago_subscription(subscription_id)
        db.set_subscription_metadata(
            current_user["telegram_id"],
            provider,
            subscription_id,
            billing_cycle,
            status="cancelled",
            expires_at=expires_at,
        )
        await _notify_cancel_at_period_end(current_user["telegram_id"], expires_at)
        return {
            "message": "La cancelacion quedó registrada y no se volverá a cobrar",
            "plan": current_user["plan"],
            "status": "cancelled",
            "expires_at": expires_at,
        }

    await deactivate_subscription(db, str(current_user["telegram_id"]), notify=True, clear_metadata=True)
    return {"message": "Suscripcion cancelada", "plan": "free", "status": "cancelled", "expires_at": None}


@router.post("/manage-billing")
async def manage_billing(
    current_user: dict = Depends(get_authenticated_user), db: Database = Depends(get_db)
):
    web_user = db.get_web_user(current_user["telegram_id"]) or {}
    provider = web_user.get("subscription_provider")
    subscription_id = web_user.get("subscription_id")

    if provider == "stripe" and subscription_id:
        return {
            "provider": "stripe",
            "url": _create_stripe_billing_portal(subscription_id),
        }

    return {
        "provider": provider,
        "url": None,
        "detail": f"Para gestionar facturación escribinos a {SUPPORT_EMAIL}",
        "support_email": SUPPORT_EMAIL,
    }


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

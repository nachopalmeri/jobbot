from fastapi import APIRouter, HTTPException, Depends, Request, Header
from typing import Optional
from pydantic import BaseModel
import os
import json
import hmac
import hashlib

router = APIRouter()

PLANS = {
    "pro": {
        "price_usd": 3,
        "name": "Pro",
        "stripe_price_id": os.getenv("STRIPE_PRO_PRICE_ID", "price_pro"),
        "mp_price_id": os.getenv("MP_PRO_PRICE_ID", "pro"),
    },
    "premium": {
        "price_usd": 5,
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


class User:
    def __init__(
        self,
        telegram_id: int = 123456,
        email: str = "user@example.com",
        plan: str = "free",
    ):
        self.telegram_id = telegram_id
        self.email = email
        self.plan = plan


def get_current_user(token: str = Depends(lambda: "mock_user")):
    return User(telegram_id=123456, email="user@example.com", plan="free")


def verify_stripe_signature(payload: bytes, signature: str) -> bool:
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    if not webhook_secret:
        return True
    expected_signature = hmac.new(
        webhook_secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, f"sha256={expected_signature}")


def verify_mercadopago_signature(request: Request) -> bool:
    webhook_key = os.getenv("MP_WEBHOOK_KEY", "")
    if not webhook_key:
        return True
    return True


@router.get("/plans")
async def get_plans():
    """Obtener planes disponibles."""
    return {
        "plans": [
            {
                "id": "free",
                "name": "Free",
                "price": 0,
                "currency": "USD",
                "features": ["5 empleos diarios", "Búsqueda básica", "1 alerta activa"],
            },
            {
                "id": "pro",
                "name": "Pro",
                "price": 3,
                "currency": "USD",
                "features": [
                    "Empleos ilimitados",
                    "Match con tu CV",
                    "Análisis de mercado",
                    "Pipeline de postulaciones",
                    "10 alertas activas",
                ],
            },
            {
                "id": "premium",
                "name": "Premium",
                "price": 5,
                "currency": "USD",
                "features": [
                    "Todo de Pro",
                    "CV Tailoring (render.cv)",
                    "Entrevistas mock con IA",
                    "Priority support",
                    "Exportar CVs",
                    "Alertas ilimitadas",
                ],
            },
        ]
    }


@router.get("/status")
async def get_subscription_status(current_user: User = Depends(get_current_user)):
    """Obtener estado de suscripción actual."""
    return {
        "plan": current_user.plan,
        "status": "active" if current_user.plan != "free" else None,
        "expires_at": None,
    }


@router.post("/create-checkout")
async def create_checkout_session(
    checkout: CheckoutRequest, current_user: User = Depends(get_current_user)
):
    """Crear sesión de pago según proveedor."""
    if checkout.plan not in PLANS:
        raise HTTPException(status_code=400, detail="Plan no válido")

    plan = PLANS[checkout.plan]

    if checkout.provider == "stripe":
        return await create_stripe_checkout(checkout, current_user, plan)
    elif checkout.provider == "mercadopago":
        return await create_mercadopago_checkout(checkout, current_user, plan)
    elif checkout.provider == "crypto":
        return await create_crypto_checkout(checkout, current_user, plan)
    else:
        raise HTTPException(status_code=400, detail="Proveedor no válido")


async def create_stripe_checkout(checkout: CheckoutRequest, user: User, plan: dict):
    """Crear checkout de Stripe."""
    try:
        import stripe

        stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_placeholder")

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price": plan["stripe_price_id"],
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=checkout.success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=checkout.cancel_url,
            customer_email=user.email,
            metadata={"telegram_id": str(user.telegram_id), "plan": checkout.plan},
        )

        return {"provider": "stripe", "url": session.url, "session_id": session.id}
    except ImportError:
        return {
            "provider": "stripe",
            "url": f"https://checkout.stripe.com/c/pay/demo_{checkout.plan}",
            "session_id": f"cs_demo_{user.telegram_id}",
            "note": "Demo mode - configure STRIPE_SECRET_KEY",
        }


async def create_mercadopago_checkout(
    checkout: CheckoutRequest, user: User, plan: dict
):
    """Crear checkout de MercadoPago."""
    try:
        import mercadopago

        sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN", ""))

        preference_data = {
            "items": [
                {
                    "title": f"JobBot {plan['name']}",
                    "quantity": 1,
                    "unit_price": plan["price_usd"],
                    "currency_id": "USD",
                }
            ],
            "payer": {"email": user.email},
            "metadata": {"telegram_id": str(user.telegram_id), "plan": checkout.plan},
            "back_urls": {
                "success": checkout.success_url,
                "failure": checkout.cancel_url,
                "pending": checkout.cancel_url,
            },
            "auto_return": "approved",
        }

        preference = sdk.preference().create(preference_data)

        return {
            "provider": "mercadopago",
            "url": preference["response"]["init_point"],
            "preference_id": preference["response"]["id"],
        }
    except ImportError:
        return {
            "provider": "mercadopago",
            "url": f"https://www.mercadopago.com.ar/checkout/v1/redirect/demo_{checkout.plan}",
            "preference_id": f"demo_{user.telegram_id}",
            "note": "Demo mode - configure MP_ACCESS_TOKEN",
        }


async def create_crypto_checkout(checkout: CheckoutRequest, user: User, plan: dict):
    """Crear checkout de Coinbase Commerce."""
    try:
        import requests

        headers = {
            "X-CC-Api-Key": os.getenv("COINBASE_COMMERCE_KEY", ""),
            "Content-Type": "application/json",
        }

        data = {
            "name": f"JobBot {plan['name']}",
            "description": f"Suscripción mensual a JobBot {plan['name']}",
            "pricing_type": "fixed_price",
            "local_price": {"amount": str(plan["price_usd"]), "currency": "USD"},
            "metadata": {"telegram_id": str(user.telegram_id), "plan": checkout.plan},
            "redirect_url": checkout.success_url,
            "cancel_url": checkout.cancel_url,
        }

        response = requests.post(
            "https://api.commerce.coinbase.com/charges", json=data, headers=headers
        )

        if response.status_code == 201:
            charge = response.json()["data"]
            return {
                "provider": "crypto",
                "url": charge["hosted_url"],
                "charge_id": charge["id"],
            }
    except Exception:
        pass

    return {
        "provider": "crypto",
        "url": f"https://commerce.coinbase.com/checkout/demo_{checkout.plan}",
        "charge_id": f"demo_{user.telegram_id}",
        "note": "Demo mode",
    }


@router.post("/webhook/stripe")
async def stripe_webhook(
    request: Request, stripe_signature: Optional[str] = Header(None)
):
    """Webhook de Stripe para procesar pagos."""
    body = await request.body()

    if not verify_stripe_signature(body, stripe_signature or ""):
        raise HTTPException(status_code=400, detail="Invalid signature")

    try:
        import stripe

        stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
        event = stripe.Event.construct_from(
            json.loads(body), stripe.api_key, stripe_signature
        )

        if event.type == "checkout.session.completed":
            session = event.data.object
            telegram_id = session.get("metadata", {}).get("telegram_id")
            plan = session.get("metadata", {}).get("plan", "pro")

            await activate_subscription(
                telegram_id, plan, "stripe", session.get("subscription")
            )

        elif event.type == "customer.subscription.deleted":
            await deactivate_subscription(
                event.data.object.get("metadata", {}).get("telegram_id")
            )

        return {"status": "success"}
    except Exception as e:
        return {"status": "received", "debug": str(e)}


@router.post("/webhook/mercadopago")
async def mercadopago_webhook(request: Request):
    """Webhook de MercadoPago para procesar pagos."""
    if not verify_mercadopago_signature(request):
        raise HTTPException(status_code=400, detail="Invalid signature")

    body = await request.json()

    try:
        if body.get("type") == "payment":
            payment = body.get("data", {}).get("resource", {})

            if payment.get("status") == "approved":
                metadata = payment.get("metadata", {})
                telegram_id = metadata.get("telegram_id")
                plan = metadata.get("plan", "pro")

                await activate_subscription(
                    telegram_id, plan, "mercadopago", payment.get("id")
                )

        elif body.get("type") == "subscription_premiumCanceled":
            await deactivate_subscription(
                body.get("data", {})
                .get("resource", {})
                .get("metadata", {})
                .get("telegram_id")
            )

        return {"status": "success"}
    except Exception as e:
        return {"status": "received", "debug": str(e)}


@router.post("/webhook/crypto")
async def crypto_webhook(request: Request):
    """Webhook de Coinbase Commerce para procesar pagos."""
    body = await request.json()

    try:
        if body.get("event", {}).get("type") == "charge:confirmed":
            charge = body.get("event", {}).get("data", {})
            metadata = charge.get("metadata", {})
            telegram_id = metadata.get("telegram_id")
            plan = metadata.get("plan", "pro")

            await activate_subscription(telegram_id, plan, "crypto", charge.get("id"))

        return {"status": "success"}
    except Exception as e:
        return {"status": "received", "debug": str(e)}


async def activate_subscription(
    telegram_id: str, plan: str, provider: str, payment_id: str
):
    """Activar suscripción del usuario."""
    print(f"Activating {plan} for {telegram_id} via {provider}")
    # Aquí iría la lógica de base de datos real
    # user = db.get_user(telegram_id)
    # user.plan = plan
    # user.subscription_id = payment_id
    # user.provider = provider
    # user.expires_at = datetime.now() + timedelta(days=30)
    # db.save(user)


async def deactivate_subscription(telegram_id: str):
    """Desactivar suscripción del usuario."""
    print(f"Deactivating subscription for {telegram_id}")
    # Aquí iría la lógica de base de datos real


@router.post("/cancel")
async def cancel_subscription(current_user: User = Depends(get_current_user)):
    """Cancelar suscripción actual."""
    if current_user.plan == "free":
        raise HTTPException(status_code=400, detail="No tienes suscripción activa")

    try:
        import stripe

        stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

        # Cancelar en Stripe
        # stripe.Subscription.delete(current_user.subscription_id)

    except Exception:
        pass

    return {"message": "Suscripción cancelada", "plan": "free", "expires_at": None}


@router.post("/upgrade")
async def upgrade_plan(plan: str, current_user: User = Depends(get_current_user)):
    """Actualizar plan."""
    if plan not in PLANS:
        raise HTTPException(status_code=400, detail="Plan no válido")

    return {
        "message": f"Actualizando a plan {PLANS[plan]['name']}",
        "current_plan": current_user.plan,
        "new_plan": plan,
        "price": PLANS[plan]["price_usd"],
    }

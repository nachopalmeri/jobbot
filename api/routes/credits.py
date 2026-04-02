"""
Credit System API Routes
Sistema de créditos para CV Suite - Compras one-time, nunca expiran
"""
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

# Configuración de packs de créditos
CREDIT_PACKS = {
    "unlock_suite": {
        "name": "CV Suite Unlock",
        "description": "Lifetime access + 50 AI credits",
        "credits": 50,
        "price_usd": 9,
        "stripe_price_id": os.getenv("STRIPE_UNLOCK_PRICE_ID"),
        "is_unlock": True,
    },
    "25_credits": {
        "name": "25 AI Credits",
        "description": "25 análisis IA",
        "credits": 25,
        "price_usd": 7,
        "stripe_price_id": os.getenv("STRIPE_25CREDITS_PRICE_ID"),
        "is_unlock": False,
    },
    "60_credits": {
        "name": "60 AI Credits",
        "description": "60 análisis IA - Best value",
        "credits": 60,
        "price_usd": 15,
        "stripe_price_id": os.getenv("STRIPE_60CREDITS_PRICE_ID"),
        "is_unlock": False,
        "highlight": True,
    },
    "150_credits": {
        "name": "150 AI Credits",
        "description": "150 análisis IA - Power user",
        "credits": 150,
        "price_usd": 29,
        "stripe_price_id": os.getenv("STRIPE_150CREDITS_PRICE_ID"),
        "is_unlock": False,
    },
}


class CreditCheckoutRequest(BaseModel):
    pack_type: str  # unlock_suite, 25_credits, 60_credits, 150_credits
    success_url: str = "https://app-jobbot.vercel.app/dashboard/creditos"
    cancel_url: str = "https://app-jobbot.vercel.app/dashboard/creditos"


class CreditBalanceResponse(BaseModel):
    total_credits: int
    unlock_active: bool
    active_packs: list


@router.get("/packs")
async def get_credit_packs():
    """Obtiene los packs de créditos disponibles para compra."""
    packs = []
    for pack_id, pack in CREDIT_PACKS.items():
        packs.append({
            "id": pack_id,
            "name": pack["name"],
            "description": pack["description"],
            "credits": pack["credits"],
            "price_usd": pack["price_usd"],
            "is_unlock": pack["is_unlock"],
            "highlight": pack.get("highlight", False),
            "unit_price": round(pack["price_usd"] / pack["credits"], 3),
        })
    
    return {
        "packs": packs,
        "note": "Los créditos nunca expiran. 1 crédito = 1 análisis IA o carta de presentación."
    }


@router.get("/balance")
async def get_credits_balance(
    current_user: dict = Depends(get_authenticated_user),
    db: Database = Depends(get_db),
):
    """Obtiene el balance actual de créditos del usuario."""
    telegram_id = current_user.get("telegram_id")
    if not telegram_id:
        raise HTTPException(status_code=400, detail="Usuario sin telegram_id")
    
    balance = db.get_user_credits_balance(telegram_id)
    
    return {
        "total_credits": balance["total_credits"],
        "unlock_active": balance["unlock_active"],
        "active_packs": balance["active_packs"],
        "features_available": {
            "cv_basic": True,  # Siempre disponible
            "cv_ai": balance["total_credits"] > 0 or current_user.get("plan") in ["pro", "premium"],
            "cv_history": balance["unlock_active"],
            "cover_letter": balance["total_credits"] > 0 or current_user.get("plan") == "premium",
        }
    }


@router.post("/checkout")
async def create_credit_checkout(
    request: CreditCheckoutRequest,
    current_user: dict = Depends(get_authenticated_user),
    db: Database = Depends(get_db),
):
    """Crea una sesión de checkout para comprar créditos."""
    telegram_id = current_user.get("telegram_id")
    if not telegram_id:
        raise HTTPException(status_code=400, detail="Usuario sin telegram_id")
    
    pack = CREDIT_PACKS.get(request.pack_type)
    if not pack:
        raise HTTPException(status_code=400, detail="Pack no válido")
    
    # Intentar crear checkout con Stripe
    stripe_key = os.getenv("STRIPE_SECRET_KEY", "").strip()
    if not stripe_key or not pack.get("stripe_price_id"):
        raise HTTPException(
            status_code=503, 
            detail="Sistema de pagos no disponible temporalmente"
        )
    
    try:
        import stripe
        stripe.api_key = stripe_key
        
        # Crear sesión de checkout
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": pack["stripe_price_id"],
                "quantity": 1,
            }],
            mode="payment",
            success_url=f"{request.success_url}?success=true&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=request.cancel_url,
            metadata={
                "telegram_id": str(telegram_id),
                "pack_type": request.pack_type,
                "credits": str(pack["credits"]),
                "is_unlock": str(pack.get("is_unlock", False)),
            },
        )
        
        return {
            "checkout_url": session.url,
            "session_id": session.id,
            "pack_type": request.pack_type,
            "credits": pack["credits"],
            "price_usd": pack["price_usd"],
        }
        
    except Exception as e:
        logger.error(f"[CREDITS] Error creando checkout: {e}")
        raise HTTPException(status_code=500, detail="Error al crear checkout")


@router.post("/webhook")
async def credit_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="stripe-signature"),
    db: Database = Depends(get_db),
):
    """Webhook para recibir notificaciones de pagos de créditos."""
    stripe_key = os.getenv("STRIPE_SECRET_KEY", "").strip()
    webhook_secret = os.getenv("STRIPE_CREDITS_WEBHOOK_SECRET", "").strip()
    
    if not stripe_key:
        raise HTTPException(status_code=503, detail="Stripe no configurado")
    
    import stripe
    stripe.api_key = stripe_key
    
    payload = await request.body()
    
    # Verificar firma si está configurada
    if webhook_secret and stripe_signature:
        try:
            event = stripe.Webhook.construct_event(
                payload, stripe_signature, webhook_secret
            )
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Firma inválida")
    else:
        # Sin verificación de firma (solo para desarrollo)
        import json
        event = json.loads(payload)
    
    # Procesar solo checkout.session.completed
    if event.get("type") == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session.get("metadata", {})
        
        telegram_id = int(metadata.get("telegram_id", 0))
        pack_type = metadata.get("pack_type")
        credits = int(metadata.get("credits", 0))
        
        if not telegram_id or not pack_type:
            logger.error("[CREDITS] Webhook sin metadata válida")
            raise HTTPException(status_code=400, detail="Metadata inválida")
        
        # Verificar si ya procesamos este pago (idempotencia)
        payment_id = session.get("id")
        existing = db._fetchone(
            "SELECT 1 FROM credit_packs WHERE payment_id = ?",
            (payment_id,)
        )
        if existing:
            return {"status": "already_processed"}
        
        # Agregar créditos al usuario
        pack_config = CREDIT_PACKS.get(pack_type, {})
        try:
            pack_db_id = db.add_credit_pack(
                telegram_id=telegram_id,
                pack_type=pack_type,
                credits=credits,
                price=pack_config.get("price_usd", 0),
                payment_provider="stripe",
                payment_id=payment_id,
                metadata={"session": session}
            )
            
            logger.info(f"[CREDITS] Agregados {credits} créditos a {telegram_id} (pack: {pack_type})")
            
            return {
                "status": "success",
                "pack_id": pack_db_id,
                "credits_added": credits,
            }
        except Exception as e:
            logger.error(f"[CREDITS] Error agregando créditos: {e}")
            raise HTTPException(status_code=500, detail="Error procesando créditos")
    
    return {"status": "ignored"}


@router.get("/transactions")
async def get_credit_transactions(
    limit: int = 50,
    current_user: dict = Depends(get_authenticated_user),
    db: Database = Depends(get_db),
):
    """Obtiene el historial de transacciones de créditos del usuario."""
    telegram_id = current_user.get("telegram_id")
    if not telegram_id:
        raise HTTPException(status_code=400, detail="Usuario sin telegram_id")
    
    transactions = db.get_credit_transactions(telegram_id, limit)
    return {
        "transactions": transactions,
        "count": len(transactions),
    }


@router.get("/feature-access/{feature}")
async def check_feature_access(
    feature: str,  # cv_basic, cv_ai, cv_history, cover_letter, interview_prep
    current_user: dict = Depends(get_authenticated_user),
    db: Database = Depends(get_db),
):
    """
    Verifica si el usuario tiene acceso a una feature específica.
    Devuelve información sobre créditos necesarios y disponibles.
    """
    telegram_id = current_user.get("telegram_id")
    if not telegram_id:
        raise HTTPException(status_code=400, detail="Usuario sin telegram_id")
    
    access = db.has_feature_access(telegram_id, feature)
    
    return {
        "feature": feature,
        "has_access": access["has_access"],
        "can_use": access["can_use"],
        "requires_credits": access["requires_credits"],
        "user_credits": access["user_credits"],
        "has_unlock": access["has_unlock"],
        "message": _get_feature_message(feature, access),
    }


def _get_feature_message(feature: str, access: dict) -> str:
    """Genera un mensaje descriptivo sobre el acceso a la feature."""
    if not access["has_access"]:
        if feature == "cv_history":
            return "Desbloqueá CV Suite para ver tu historial completo"
        return "Feature no disponible en tu plan"
    
    if not access["can_use"]:
        return f"Necesitás {access['requires_credits']} crédito(s). Tenés {access['user_credits']}."
    
    if access["requires_credits"] > 0:
        return f"Disponible. Consumirá {access['requires_credits']} crédito(s)."
    
    return "Disponible sin costo"

import os

from fastapi import APIRouter, Depends

try:
    from job_bot.database import Database
    from job_bot import config
except ImportError:
    from database import Database
    import config


router = APIRouter()


def _configured(name: str) -> bool:
    return bool((os.getenv(name) or "").strip())


def _stripe_ready() -> bool:
    required = [
        "STRIPE_SECRET_KEY",
        "STRIPE_WEBHOOK_SECRET",
        "STRIPE_STARTER_PRICE_ID",
        "STRIPE_PRO_PRICE_ID",
        "STRIPE_PREMIUM_PRICE_ID",
        "STRIPE_STARTER_YEARLY_PRICE_ID",
        "STRIPE_PRO_YEARLY_PRICE_ID",
        "STRIPE_PREMIUM_YEARLY_PRICE_ID",
        "STRIPE_UNLOCK_PRICE_ID",
        "STRIPE_25CREDITS_PRICE_ID",
        "STRIPE_60CREDITS_PRICE_ID",
        "STRIPE_150CREDITS_PRICE_ID",
        "STRIPE_CREDITS_WEBHOOK_SECRET",
    ]
    return all(_configured(key) for key in required)


def _mercadopago_ready() -> bool:
    required = [
        "MP_ACCESS_TOKEN",
        "MP_WEBHOOK_SECRET",
    ]
    return all(_configured(key) for key in required)


def _mercadopago_status() -> str:
    required = [
        "MP_ACCESS_TOKEN",
        "MP_WEBHOOK_SECRET",
    ]
    configured = [_configured(key) for key in required]
    if all(configured):
        return "configured"
    if any(configured):
        return "partial"
    return "missing"


def get_db() -> Database:
    return Database()


@router.get("/stats")
async def get_public_stats(db: Database = Depends(get_db)):
    stats = db.get_stats()
    stats["sources_count"] = sum(1 for enabled in config.SOURCES_ENABLED.values() if enabled)
    stats["check_interval_hours"] = config.DEFAULT_CHECK_INTERVAL_HOURS
    return stats


@router.get("/health")
async def health_check(db: Database = Depends(get_db)):
    checks = {
        "database": "ok",
        "stripe": "configured" if _stripe_ready() else "missing",
        "mercadopago": _mercadopago_status(),
        "groq": "configured" if os.getenv("GROQ_API_KEY") else "missing",
    }

    try:
        db.get_stats()
    except Exception:
        checks["database"] = "error"

    overall = "ok" if checks["database"] == "ok" else "degraded"
    return {"status": overall, "checks": checks}

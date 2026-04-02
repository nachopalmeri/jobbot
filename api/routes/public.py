import os

from fastapi import APIRouter, Depends

try:
    from job_bot.database import Database
    from job_bot import config
except ImportError:
    from database import Database
    import config


router = APIRouter()


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
        "stripe": "configured" if os.getenv("STRIPE_SECRET_KEY") else "missing",
        "mercadopago": "configured" if os.getenv("MP_ACCESS_TOKEN") else "missing",
        "groq": "configured" if os.getenv("GROQ_API_KEY") else "missing",
    }

    try:
        db.get_stats()
    except Exception:
        checks["database"] = "error"

    overall = "ok" if checks["database"] == "ok" else "degraded"
    return {"status": overall, "checks": checks}

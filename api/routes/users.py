from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel

try:
    from job_bot.database import Database
except ImportError:
    from database import Database

from .auth import get_authenticated_user, get_db


router = APIRouter()


PLAN_LIMITS = {
    "free": {"ai_analyses_limit": 0, "searches_limit": 3, "interviews_limit": 0},
    "starter": {"ai_analyses_limit": 0, "searches_limit": 12, "interviews_limit": 0},
    "pro": {"ai_analyses_limit": 4, "searches_limit": 40, "interviews_limit": 0},
    "premium": {"ai_analyses_limit": 20, "searches_limit": 120, "interviews_limit": 10},
}


class PreferencesUpdate(BaseModel):
    experience_level: str = "junior"
    role_type: str = ""
    technologies: str = ""
    job_modality: str = "cualquiera"
    max_job_age_days: int = 30
    match_threshold: int = 70
    alert_channel: str = "telegram"
    check_interval_hours: int = 6
    alert_start_hour: int = 8
    alert_end_hour: int = 22
    timezone: str = "America/Buenos_Aires"
    weekly_goal: int = 10
    digest_mode: str = "realtime"
    active_alerts: bool = False
    blocked_companies: str = ""
    preferred_companies: str = ""


def _parse_application_datetime(raw_value):
    if not raw_value:
        return None

    if isinstance(raw_value, datetime):
        dt = raw_value
    elif isinstance(raw_value, str):
        try:
            dt = datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _compute_application_streak(apps: list[dict]) -> int:
    application_days = set()
    for app in apps:
        parsed = _parse_application_datetime(app.get("applied_at") or app.get("created_at"))
        if parsed:
            application_days.add(parsed.date())

    if not application_days:
        return 0

    today = datetime.now(timezone.utc).date()
    if today in application_days:
        cursor = today
    elif today - timedelta(days=1) in application_days:
        cursor = today - timedelta(days=1)
    else:
        return 0

    streak = 0
    while cursor in application_days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def _build_daily_motivation(weekly_goal: int, weekly_applied: int, streak: int) -> str:
    if weekly_goal > 0 and weekly_applied >= weekly_goal:
        return "Ya cumpliste tu meta semanal. Ahora conviene priorizar calidad sobre ansiedad."
    if streak >= 5:
        return f"Llevas {streak} dias de constancia. Una buena rutina gana mas que un sprint."

    remaining = max(weekly_goal - weekly_applied, 0)
    if remaining > 0:
        return f"Te faltan {remaining} postulaciones para cerrar tu meta semanal. Hoy una buena aplicacion ya suma."
    return "No hace falta resolver toda la busqueda hoy. Enfocate en una mejora concreta."


def _build_dashboard_payload(db: Database, telegram_id: int) -> dict:
    profile = db.get_user_profile(telegram_id)
    schedule = db.get_user_schedule(telegram_id)
    apps = db.get_user_applications(telegram_id)
    weekly_goal = db.get_weekly_goal(telegram_id)
    weekly_applied = db.get_weekly_applications_count(telegram_id)
    application_streak = _compute_application_streak(apps)
    funnel = {
        "applied": len([a for a in apps if a.get("status") == "aplicado"]),
        "interview": len([a for a in apps if a.get("status") == "entrevista"]),
        "rejected": len([a for a in apps if a.get("status") == "rechazado"]),
        "offer": len([a for a in apps if a.get("status") == "oferta"]),
    }
    company_filters = db.get_company_filters(telegram_id)

    return {
        "telegram_id": str(telegram_id),
        "plan": db.get_user_plan(telegram_id),
        "is_admin": db.is_admin(telegram_id),
        "has_telegram_link": telegram_id > 0,
        "account_type": "telegram-linked" if telegram_id > 0 else "web-only",
        "user_level": profile.get("experience_level", "junior"),
        "user_role": profile.get("role_type", ""),
        "weekly_goal": weekly_goal,
        "weekly_applied": weekly_applied,
        "weekly_remaining": max(weekly_goal - weekly_applied, 0),
        "application_streak": application_streak,
        "daily_motivation": _build_daily_motivation(
            weekly_goal,
            weekly_applied,
            application_streak,
        ),
        "funnel": funnel,
        "applications": apps,
        "digest_mode": db.get_digest_mode(telegram_id),
        "active_alerts": bool((db.get_user(telegram_id) or {}).get("active_alerts")),
        "blocked_companies": company_filters.get("blocked_raw", ""),
        "preferred_companies": company_filters.get("preferred_raw", ""),
        "check_interval_hours": schedule.get("check_interval_hours", 6),
        "alert_start_hour": schedule.get("alert_start_hour", 8),
        "alert_end_hour": schedule.get("alert_end_hour", 22),
        "timezone": schedule.get("timezone", "America/Buenos_Aires"),
    }


@router.get("/me")
async def get_me(current_user: dict = Depends(get_authenticated_user)):
    return {
        "telegram_id": current_user["telegram_id"],
        "email": current_user["email"],
        "plan": current_user["plan"],
        "is_admin": current_user["is_admin"],
        "has_telegram_link": current_user.get(
            "has_telegram_link", current_user["telegram_id"] > 0
        ),
        "account_type": (
            "telegram-linked" if current_user["telegram_id"] > 0 else "web-only"
        ),
        "is_temp_account": current_user["telegram_id"] <= 0,
        "name": current_user["name"],
    }


@router.get("/usage")
async def get_usage(
    current_user: dict = Depends(get_authenticated_user), db: Database = Depends(get_db)
):
    telegram_id = current_user["telegram_id"]
    web_user = db.get_web_user(telegram_id) or {}
    plan = db.get_user_plan(telegram_id)
    plan_limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])

    ai_used = int(web_user.get("ai_analyses_used") or 0)
    searches_used = int(web_user.get("searches_used") or 0)
    interviews_used = int(web_user.get("interviews_used") or 0)
    ai_limit = int(web_user.get("ai_analyses_limit") or plan_limits["ai_analyses_limit"])
    searches_limit = int(web_user.get("searches_limit") or plan_limits["searches_limit"])
    interviews_limit = int(web_user.get("interviews_limit") or plan_limits["interviews_limit"])

    return {
        "ai_analyses_used": ai_used,
        "ai_analyses_limit": ai_limit,
        "searches_used": searches_used,
        "searches_limit": searches_limit,
        "interviews_used": interviews_used,
        "interviews_limit": interviews_limit,
        "remaining_analyses": max(0, ai_limit - ai_used),
        "remaining_searches": max(0, searches_limit - searches_used),
        "remaining_interviews": max(0, interviews_limit - interviews_used),
    }


@router.get("/dashboard")
async def get_dashboard(
    current_user: dict = Depends(get_authenticated_user), db: Database = Depends(get_db)
):
    return _build_dashboard_payload(db, current_user["telegram_id"])


@router.get("/preferences")
async def get_preferences(
    current_user: dict = Depends(get_authenticated_user), db: Database = Depends(get_db)
):
    telegram_id = current_user["telegram_id"]
    profile = db.get_user_profile(telegram_id)
    schedule = db.get_user_schedule(telegram_id)
    company_filters = db.get_company_filters(telegram_id)

    return {
        **profile,
        "alert_channel": (db.get_user(telegram_id) or {}).get("alert_channel", "telegram"),
        "check_interval_hours": schedule.get("check_interval_hours", 6),
        "alert_start_hour": schedule.get("alert_start_hour", 8),
        "alert_end_hour": schedule.get("alert_end_hour", 22),
        "timezone": schedule.get("timezone", "America/Buenos_Aires"),
        "weekly_goal": db.get_weekly_goal(telegram_id),
        "digest_mode": db.get_digest_mode(telegram_id),
        "active_alerts": bool((db.get_user(telegram_id) or {}).get("active_alerts")),
        "blocked_companies": company_filters.get("blocked_raw", ""),
        "preferred_companies": company_filters.get("preferred_raw", ""),
    }


@router.post("/preferences")
async def update_preferences(
    payload: PreferencesUpdate,
    current_user: dict = Depends(get_authenticated_user),
    db: Database = Depends(get_db),
):
    telegram_id = current_user["telegram_id"]
    db.set_user_profile(
        telegram_id,
        payload.experience_level,
        payload.role_type,
        payload.technologies,
        payload.job_modality,
        payload.max_job_age_days,
        payload.match_threshold,
    )
    db.set_user_schedule(
        telegram_id,
        payload.check_interval_hours,
        payload.alert_start_hour,
        payload.alert_end_hour,
        payload.timezone,
    )
    db.set_alert_channel(telegram_id, payload.alert_channel)
    db.set_digest_mode(telegram_id, payload.digest_mode)
    db.set_alerts_active(telegram_id, payload.active_alerts)
    db.set_weekly_goal(telegram_id, payload.weekly_goal)
    db.set_company_filters(
        telegram_id,
        payload.blocked_companies,
        payload.preferred_companies,
    )

    return {
        "ok": True,
        "message": "Preferencias actualizadas",
        "preferences": await get_preferences(current_user, db),
    }

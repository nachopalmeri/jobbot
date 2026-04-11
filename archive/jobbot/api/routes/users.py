from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel

try:
    from job_bot.database import Database
    from job_bot.cv_analyzer import extract_keywords, parse_cv
except ImportError:
    from database import Database
    from cv_analyzer import extract_keywords, parse_cv

from .auth import get_authenticated_user, get_db, _create_telegram_link_code_payload
from ..core.cache import CacheManager, cache, user_dashboard_key


router = APIRouter()


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


def _safe_int(value, default: int) -> int:
    try:
        return default if value is None else int(value)
    except (TypeError, ValueError):
        return default


def _profile_from_user(user: dict) -> dict:
    return {
        "experience_level": user.get("experience_level", "junior"),
        "role_type": user.get("role_type", ""),
        "technologies": user.get("technologies", ""),
        "job_modality": user.get("job_modality", "cualquiera"),
        "max_job_age_days": _safe_int(user.get("max_job_age_days"), 30),
        "match_threshold": _safe_int(user.get("match_threshold"), 70),
    }


def _schedule_from_user(user: dict) -> dict:
    return {
        "check_interval_hours": _safe_int(user.get("check_interval_hours"), 6),
        "alert_start_hour": _safe_int(user.get("alert_start_hour"), 8),
        "alert_end_hour": _safe_int(user.get("alert_end_hour"), 22),
        "timezone": user.get("timezone") or "America/Buenos_Aires",
    }


def _company_filters_from_user(user: dict) -> dict:
    blocked_raw = user.get("blocked_companies") or ""
    preferred_raw = user.get("preferred_companies") or ""

    def _to_set(raw: str):
        items = []
        for part in raw.split(","):
            name = part.strip()
            if name:
                items.append(name.lower())
        return set(items)

    return {
        "blocked": _to_set(blocked_raw),
        "preferred": _to_set(preferred_raw),
        "blocked_raw": blocked_raw,
        "preferred_raw": preferred_raw,
    }


def _invalidate_dashboard_cache(telegram_id: int):
    cache.delete("users", user_dashboard_key(telegram_id))


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


def _build_daily_motivation(weekly_goal: int, weekly_applied: int, streak: int, cv_score: int | None) -> str:
    if weekly_goal > 0 and weekly_applied >= weekly_goal:
        return "Ya cumpliste tu meta semanal. Hoy conviene elegir mejor, no aplicar por inercia."
    if streak >= 5:
        return f"Llevás {streak} días con constancia. Una búsqueda sostenida vale más que un sprint de ansiedad."
    if cv_score is not None and cv_score < 65:
        return "Tu siguiente salto no es aplicar más: es subir la calidad del CV para que el match trabaje a tu favor."
    if weekly_goal > 0:
        remaining = max(weekly_goal - weekly_applied, 0)
        if remaining > 0:
            return f"Te faltan {remaining} aplicaciones para cerrar la meta semanal. Una buena postulación hoy ya cambia el ritmo."
    return "No hace falta resolver toda la búsqueda hoy. Alcanzá una mejora concreta y dejá el sistema haciendo el resto."


def _build_coaching_tips(
    weekly_goal: int,
    weekly_applied: int,
    funnel: dict,
    cv_uploaded: bool,
    cv_score: int | None,
) -> list[str]:
    tips: list[str] = []

    if not cv_uploaded:
        tips.append("Subí tu CV al dashboard para activar el rating, recomendaciones y mejor contexto de match.")
    elif cv_score is not None and cv_score < 70:
        tips.append("Antes de aplicar en volumen, reforzá el CV con tecnologías y logros concretos que ya tenés.")

    if weekly_goal > 0 and weekly_applied < weekly_goal:
        tips.append("Tu meta semanal está por debajo del ritmo esperado. Reservá una sesión corta hoy para sumar 1 o 2 aplicaciones.")

    applied = funnel.get("applied", 0)
    interviews = funnel.get("interview", 0)
    if applied >= 5 and interviews == 0:
        tips.append("Hay volumen pero no entrevistas. Revisá el CV y subí el match mínimo para priorizar vacantes más alineadas.")
    elif interviews > 0 and funnel.get("offer", 0) == 0:
        tips.append("Ya lograste entrevistas. El foco ahora es preparar respuestas y seguimiento, no abrir más búsquedas.")

    if not tips:
        tips.append("Tu proceso está bastante equilibrado. Mantené constancia y usá los matches para elegir calidad sobre cantidad.")

    return tips[:3]


def _build_cv_insights(
    db: Database,
    telegram_id: int,
    user: dict | None = None,
    profile: dict | None = None,
) -> dict:
    user = user or db.get_user(telegram_id) or {}
    profile = profile or _profile_from_user(user)
    cv_path = user.get("cv_path")
    if not cv_path:
        return {
            "uploaded": False,
            "file_name": None,
            "score": None,
            "strengths": [],
            "improvements": [
                "Subí tu CV para evaluar cobertura de tecnologías, claridad y nivel de preparación."
            ],
            "top_keywords": [],
            "missing_keywords": [],
            "summary": "Todavía no cargaste un CV en la cuenta.",
        }

    cv_text = parse_cv(cv_path)
    file_name = Path(cv_path).name
    if not cv_text:
        return {
            "uploaded": True,
            "file_name": file_name,
            "score": None,
            "strengths": [],
            "improvements": [
                "No pude leer el archivo actual. Probá subir un PDF o TXT más limpio."
            ],
            "top_keywords": [],
            "missing_keywords": [],
            "summary": "Hay un CV guardado, pero no se pudo procesar su contenido.",
        }

    keywords = extract_keywords(cv_text)
    tech_keywords = keywords.get("tech", [])
    soft_keywords = keywords.get("soft", [])

    expected_terms = []
    for term in (profile.get("technologies") or "").split(","):
        clean = term.strip().lower()
        if clean:
            expected_terms.append(clean)
    role_terms = [part.strip().lower() for part in (profile.get("role_type") or "").split() if part.strip()]
    expected_terms.extend(role_terms[:3])
    expected_unique = sorted(set(expected_terms))

    text_lower = cv_text.lower()
    matched_expected = [term for term in expected_unique if term in text_lower]
    missing_expected = [term for term in expected_unique if term not in text_lower]

    coverage_ratio = 1.0 if not expected_unique else len(matched_expected) / len(expected_unique)
    density_ratio = min(len(tech_keywords) / 12, 1)
    length_ratio = min(len(cv_text) / 2200, 1)
    score = int(min(100, round((coverage_ratio * 55) + (density_ratio * 25) + (length_ratio * 20))))

    strengths: list[str] = []
    if tech_keywords:
        strengths.append(f"El CV ya muestra stack técnico reconocible: {', '.join(tech_keywords[:5])}.")
    if soft_keywords:
        strengths.append(f"También aparecen señales blandas útiles: {', '.join(soft_keywords[:3])}.")
    if coverage_ratio >= 0.65 and expected_unique:
        strengths.append("La mayor parte de las tecnologías que configuraste ya aparecen dentro del CV.")
    if len(cv_text) >= 1500:
        strengths.append("El contenido tiene suficiente cuerpo para explicar experiencia y proyectos.")

    improvements: list[str] = []
    if missing_expected:
        improvements.append(f"Te conviene reflejar mejor estas keywords objetivo: {', '.join(missing_expected[:5])}.")
    if len(cv_text) < 1200:
        improvements.append("El CV se ve corto. Sumá logros, impacto y contexto de proyectos para ganar claridad.")
    if len(soft_keywords) == 0:
        improvements.append("No aparecen señales de colaboración, ownership o comunicación. Podés agregarlas en experiencias.")
    if not improvements:
        improvements.append("El CV está parejo. El siguiente paso es personalizarlo según las vacantes que más te interesen.")

    if score >= 80:
        summary = "Tu CV está bien preparado para empezar a priorizar vacantes por calidad."
    elif score >= 65:
        summary = "Tu base es buena, pero todavía hay margen claro para mejorar cómo se vende tu perfil."
    else:
        summary = "Hoy conviene trabajar el CV antes de empujar más volumen de aplicaciones."

    return {
        "uploaded": True,
        "file_name": file_name,
        "score": score,
        "strengths": strengths[:3],
        "improvements": improvements[:4],
        "top_keywords": tech_keywords[:8],
        "missing_keywords": missing_expected[:6],
        "summary": summary,
    }


def _build_dashboard_payload(db: Database, telegram_id: int) -> dict:
    user = db.get_user(telegram_id) or {}
    profile = _profile_from_user(user)
    schedule = _schedule_from_user(user)
    apps = db.get_user_applications(telegram_id, limit=12)
    streak_apps = db.get_user_applications(telegram_id, limit=60)
    funnel = db.get_application_funnel_counts(telegram_id)
    company_filters = _company_filters_from_user(user)
    cv_insights = _build_cv_insights(db, telegram_id, user=user, profile=profile)
    weekly_goal = _safe_int(user.get("weekly_goal_apps"), 0)
    weekly_applied = db.get_weekly_applications_count(telegram_id)
    streak = _compute_application_streak(streak_apps)

    return {
        "telegram_id": str(telegram_id),
        "plan": db.get_user_plan(telegram_id),
        "has_telegram_link": telegram_id > 0,
        "account_type": "telegram-linked" if telegram_id > 0 else "web-only",
        "user_level": profile.get("experience_level", "junior"),
        "user_role": profile.get("role_type", ""),
        "weekly_goal": weekly_goal,
        "weekly_applied": weekly_applied,
        "weekly_remaining": max(weekly_goal - weekly_applied, 0),
        "funnel": funnel,
        "applications": apps,
        "application_streak": streak,
        "daily_motivation": _build_daily_motivation(
            weekly_goal,
            weekly_applied,
            streak,
            cv_insights.get("score"),
        ),
        "coaching_tips": _build_coaching_tips(
            weekly_goal,
            weekly_applied,
            funnel,
            cv_insights.get("uploaded", False),
            cv_insights.get("score"),
        ),
        "cv_insights": cv_insights,
        "digest_mode": (user.get("digest_mode") or "realtime").lower(),
        "active_alerts": bool(user.get("active_alerts")),
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
        "name": current_user["name"],
        "has_telegram_link": current_user["telegram_id"] > 0,
        "account_type": "telegram-linked" if current_user["telegram_id"] > 0 else "web-only",
    }


@router.get("/usage")
async def get_usage(
    current_user: dict = Depends(get_authenticated_user), db: Database = Depends(get_db)
):
    telegram_id = current_user["telegram_id"]
    web_user = db.get_web_user(telegram_id) or {}
    plan = db.get_user_plan(telegram_id)

    ai_used = int(web_user.get("ai_analyses_used") or 0)
    searches_used = int(web_user.get("searches_used") or 0)
    if plan == "free":
        ai_limit = 0
        searches_limit = 5
    elif plan == "starter":
        ai_limit = 0
        searches_limit = 30
    elif plan == "pro":
        ai_limit = 5
        searches_limit = 80
    elif plan == "premium":
        ai_limit = 30
        searches_limit = 0
    else:
        ai_limit = 0
        searches_limit = 0

    return {
        "ai_analyses_used": ai_used,
        "ai_analyses_limit": ai_limit,
        "searches_used": searches_used,
        "searches_limit": searches_limit,
        "remaining_analyses": max(0, ai_limit - ai_used),
        "remaining_searches": max(0, searches_limit - searches_used),
    }


@router.get("/dashboard")
async def get_dashboard(
    current_user: dict = Depends(get_authenticated_user), db: Database = Depends(get_db)
):
    telegram_id = current_user["telegram_id"]
    cache_key = user_dashboard_key(telegram_id)
    cached = cache.get("users", cache_key)
    if cached:
        return cached

    payload = _build_dashboard_payload(db, telegram_id)
    cache.set("users", cache_key, payload, ttl=CacheManager.TTL_SHORT)
    return payload


@router.get("/applications")
async def get_applications(
    current_user: dict = Depends(get_authenticated_user),
    db: Database = Depends(get_db),
):
    telegram_id = current_user["telegram_id"]
    return {
        "applications": db.get_user_applications(telegram_id),
        "funnel": db.get_application_funnel_counts(telegram_id),
        "weekly_goal": _safe_int((db.get_user(telegram_id) or {}).get("weekly_goal_apps"), 0),
        "weekly_applied": db.get_weekly_applications_count(telegram_id),
    }


@router.get("/preferences")
async def get_preferences(
    current_user: dict = Depends(get_authenticated_user), db: Database = Depends(get_db)
):
    telegram_id = current_user["telegram_id"]
    user = db.get_user(telegram_id) or {}
    profile = _profile_from_user(user)
    schedule = _schedule_from_user(user)
    company_filters = _company_filters_from_user(user)

    return {
        **profile,
        "alert_channel": (user.get("alert_channel") or "telegram").lower(),
        "check_interval_hours": schedule.get("check_interval_hours", 6),
        "alert_start_hour": schedule.get("alert_start_hour", 8),
        "alert_end_hour": schedule.get("alert_end_hour", 22),
        "timezone": schedule.get("timezone", "America/Buenos_Aires"),
        "weekly_goal": _safe_int(user.get("weekly_goal_apps"), 0),
        "digest_mode": (user.get("digest_mode") or "realtime").lower(),
        "active_alerts": bool(user.get("active_alerts")),
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
    _invalidate_dashboard_cache(telegram_id)

    return {
        "ok": True,
        "message": "Preferencias actualizadas",
        "preferences": await get_preferences(current_user, db),
    }


@router.post("/telegram-link-code")
async def create_telegram_link_code_alias(
    current_user: dict = Depends(get_authenticated_user),
    db: Database = Depends(get_db),
):
    return _create_telegram_link_code_payload(current_user, db)

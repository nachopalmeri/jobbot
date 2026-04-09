import hashlib
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

try:
    from job_bot.database import Database
    from job_bot.job_scraper import JobScraper
    from job_bot.cv_analyzer import build_profile_context, compare_cv_with_offer
except ImportError:
    from database import Database
    from job_scraper import JobScraper
    from cv_analyzer import build_profile_context, compare_cv_with_offer

from .auth import get_authenticated_user


router = APIRouter()


def get_db() -> Database:
    return Database()


def get_scraper() -> JobScraper:
    return JobScraper()


def _normalize_modality(value: str) -> str:
    mapping = {
        "remote": "remoto",
        "hybrid": "hibrido",
        "onsite": "presencial",
        "all": "cualquiera",
        "cualquiera": "cualquiera",
        "remoto": "remoto",
        "hibrido": "hibrido",
        "hibrido": "hibrido",
        "presencial": "presencial",
    }
    return mapping.get((value or "").strip().lower(), "cualquiera")


def _normalize_schedule(value: str) -> str:
    mapping = {
        "all": "cualquiera",
        "cualquiera": "cualquiera",
        "full_time": "full_time",
        "full-time": "full_time",
        "fulltime": "full_time",
        "jornada completa": "full_time",
        "part_time": "part_time",
        "part-time": "part_time",
        "parttime": "part_time",
        "media jornada": "part_time",
    }
    return mapping.get((value or "").strip().lower(), "cualquiera")


def _serialize_modality(job: dict) -> str:
    text = (
        f"{job.get('title', '')} {job.get('location', '')} {job.get('description', '')}"
    ).lower()
    if any(
        token in text for token in ("remoto", "remote", "anywhere", "worldwide", "wfh")
    ):
        return "remote"
    if any(token in text for token in ("hibrido", "hybrid")):
        return "hybrid"
    return "onsite"


def _extract_tags(job: dict) -> list[str]:
    text = f"{job.get('title', '')} {job.get('description', '')}".lower()
    candidates = [
        "python",
        "javascript",
        "typescript",
        "react",
        "node",
        "sql",
        "aws",
        "docker",
        "java",
        "golang",
    ]
    return [tag for tag in candidates if tag in text][:5]


def _extract_salary(job: dict) -> tuple[Optional[int], Optional[int], Optional[str]]:
    description = job.get("description", "") or ""
    match = re.search(
        r"(USD|ARS|EUR|\$)\s?([\d,]{2,})\s?[-–]\s?(USD|ARS|EUR|\$)?\s?([\d,]{2,})",
        description,
    )
    if not match:
        return None, None, None

    min_raw = match.group(2).replace(",", "")
    max_raw = match.group(4).replace(",", "")
    currency = match.group(1) or match.group(3) or "USD"
    try:
        return int(min_raw), int(max_raw), currency
    except ValueError:
        return None, None, None


def _score_job(job: dict, query: str, profile: dict, tags_filter: list[str]) -> int:
    haystack = (
        f"{job.get('title', '')} {job.get('description', '')} {job.get('company', '')}"
    ).lower()
    profile_context = build_profile_context(profile)
    analysis = compare_cv_with_offer(profile_context, haystack) if profile_context else {"score": 45}
    score = int(analysis["score"])

    terms = [part.strip().lower() for part in query.split() if part.strip()]

    for term in terms[:5]:
        if term in haystack:
            score += 4

    for tag in tags_filter:
        if tag in haystack:
            score += 3

    modality = _serialize_modality(job)
    target_modality = _normalize_modality(profile.get("job_modality") or "cualquiera")
    if target_modality == "cualquiera" or modality == {
        "remoto": "remote",
        "hibrido": "hybrid",
        "presencial": "onsite",
    }.get(target_modality):
        score += 5
    else:
        score -= 8

    return max(0, min(95, score))


def _serialize_job(job: dict, score: int) -> dict:
    salary_min, salary_max, salary_currency = _extract_salary(job)
    job_url = job.get("url") or ""
    job_id = (
        hashlib.md5(job_url.encode("utf-8")).hexdigest()
        if job_url
        else hashlib.md5(
            f"{job.get('title', '')}:{job.get('company', '')}".encode("utf-8")
        ).hexdigest()
    )
    return {
        "id": job_id,
        "title": job.get("title", "Sin titulo"),
        "company": job.get("company", "N/A"),
        "location": job.get("location", "N/A"),
        "modality": _serialize_modality(job),
        "salary_min": salary_min,
        "salary_max": salary_max,
        "salary_currency": salary_currency,
        "posted_at": job.get("date") or "",
        "match_score": score,
        "tags": _extract_tags(job),
        "description": job.get("description", "")[:400],
        "url": job_url,
        "source": job.get("source", "Unknown"),
    }


class TrackRequest(BaseModel):
    job_title: str
    company: str
    url: str
    notes: Optional[str] = None


class UpdateApplicationRequest(BaseModel):
    status: str


def _require_search_quota(db: Database, telegram_id: int):
    if not db.check_usage_limit(telegram_id, "searches"):
        raise HTTPException(
            status_code=429,
            detail="Alcanzaste el limite diario de busquedas para tu plan actual",
        )


@router.get("/search")
async def search_jobs(
    q: str = Query("", description="Query de busqueda"),
    modality: Optional[str] = Query("all", description="remote, hybrid, onsite"),
    schedule: Optional[str] = Query("all", description="full_time, part_time"),
    location: Optional[str] = Query(None, description="Ubicacion"),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    max_age_days: Optional[int] = Query(None, ge=1, le=365),
    match_threshold: Optional[int] = Query(None, ge=50, le=95),
    tags: Optional[str] = Query(None, description="Lista CSV de tags"),
    db: Database = Depends(get_db),
    scraper: JobScraper = Depends(get_scraper),
    current_user: dict = Depends(get_authenticated_user),
):
    telegram_id = current_user["telegram_id"]
    user = db.get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    _require_search_quota(db, telegram_id)

    profile = db.get_user_profile(telegram_id)
    search_location = location or user.get("location") or "Buenos Aires Argentina"
    threshold = match_threshold or profile.get("match_threshold", 70)
    tags_filter = [tag.strip().lower() for tag in (tags or "").split(",") if tag.strip()]

    query_keywords = [q.strip()] if q.strip() else db.get_user_keywords(telegram_id)
    if not query_keywords:
        query_keywords = db.generate_smart_keywords(telegram_id)
    if not query_keywords:
        query_keywords = ["python junior"]

    jobs = scraper.search_all(
        query_keywords,
        search_location,
        max_age_days=max_age_days or profile.get("max_job_age_days", 30),
    )
    jobs = JobScraper.apply_negative_filter(
        jobs, experience_level=profile.get("experience_level", "junior")
    )

    requested_modality = _normalize_modality(modality or "all")
    if requested_modality != "cualquiera":
        jobs = JobScraper.apply_modality_filter(jobs, requested_modality)

    requested_schedule = _normalize_schedule(schedule or "all")
    if requested_schedule != "cualquiera":
        jobs = JobScraper.apply_schedule_filter(jobs, requested_schedule)

    jobs = JobScraper.apply_profile_relevance_filter(
        jobs,
        role_type=profile.get("role_type", ""),
        technologies=profile.get("technologies", ""),
    )

    if tags_filter:
        jobs = [
            job
            for job in jobs
            if all(
                tag in f"{job.get('title', '')} {job.get('description', '')}".lower()
                for tag in tags_filter
            )
        ]

    serialized = []
    for job in jobs:
        score = _score_job(job, q, profile, tags_filter)
        if score < threshold:
            continue
        serialized.append(_serialize_job(job, score))

    serialized.sort(key=lambda item: item["match_score"], reverse=True)
    total = len(serialized)
    effective_limit = min(limit, 3) if current_user["plan"] == "free" else limit
    paginated = serialized[offset : offset + effective_limit]
    db.increment_usage(telegram_id, "searches")

    return {
        "jobs": paginated,
        "total": total,
        "offset": offset,
        "limit": effective_limit,
        "query": q,
    }


@router.get("/recommended")
async def get_recommended_jobs(
    db: Database = Depends(get_db),
    scraper: JobScraper = Depends(get_scraper),
    current_user: dict = Depends(get_authenticated_user),
):
    profile = db.get_user_profile(current_user["telegram_id"])
    role = profile.get("role_type") or "developer"
    return await search_jobs(
        q=role,
        db=db,
        scraper=scraper,
        current_user=current_user,
    )


@router.post("/track")
async def track_application(
    payload: TrackRequest,
    db: Database = Depends(get_db),
    current_user: dict = Depends(get_authenticated_user),
):
    telegram_id = current_user["telegram_id"]
    if current_user["plan"] == "free":
        raise HTTPException(
            status_code=403,
            detail="El pipeline de postulaciones requiere Plan Pro o Premium",
        )

    db.create_user_if_not_exists(telegram_id, current_user["name"])
    db.add_application(
        telegram_id,
        payload.job_title,
        payload.company,
        payload.url,
        payload.notes or "",
    )
    apps = db.get_user_applications(telegram_id)
    created = apps[0] if apps else {}
    return {
        "id": created.get("id"),
        "job_title": payload.job_title,
        "company": payload.company,
        "url": payload.url,
        "status": created.get("status", "aplicado"),
        "applied_at": created.get("applied_at"),
        "notes": created.get("notes"),
    }


@router.get("/applications")
async def get_applications(
    db: Database = Depends(get_db),
    current_user: dict = Depends(get_authenticated_user),
):
    return {"applications": db.get_user_applications(current_user["telegram_id"])}


@router.patch("/applications/{app_id}")
async def update_application(
    app_id: int,
    payload: UpdateApplicationRequest,
    db: Database = Depends(get_db),
    current_user: dict = Depends(get_authenticated_user),
):
    db.update_application_status(app_id, current_user["telegram_id"], payload.status)
    return {"id": app_id, "status": payload.status, "message": "Estado actualizado"}

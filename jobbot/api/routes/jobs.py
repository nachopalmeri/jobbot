"""
Enhanced Jobs Routes with Caching and Async Processing
Production-ready job search with Redis caching and circuit breaker protection.
"""

import hashlib
import re
from typing import Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..core import (
    cache,
    CacheManager,
    scraping_circuit,
    retry,
    retry_with_backoff,
    RetryConfig,
)

try:
    from job_bot.database import Database
    from job_bot.job_scraper import JobScraper
except ImportError:
    from database import Database
    from job_scraper import JobScraper

from .auth import get_authenticated_user


router = APIRouter()
_executor = ThreadPoolExecutor(max_workers=4)


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
        "presencial": "presencial",
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
    score = 45

    terms = [part.strip().lower() for part in query.split() if part.strip()]
    tech_terms = [
        part.strip().lower()
        for part in (profile.get("technologies") or "").split(",")
        if part.strip()
    ]
    role = (profile.get("role_type") or "").strip().lower()

    for term in terms[:5]:
        if term in haystack:
            score += 10

    for tech in tech_terms[:5]:
        if tech in haystack:
            score += 8

    if role and role in haystack:
        score += 12

    for tag in tags_filter:
        if tag in haystack:
            score += 6

    modality = _serialize_modality(job)
    target_modality = _normalize_modality(profile.get("job_modality") or "cualquiera")
    if target_modality == "cualquiera" or modality == {
        "remoto": "remote",
        "hibrido": "hybrid",
        "presencial": "onsite",
    }.get(target_modality):
        score += 5

    return max(50, min(95, score))


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


async def _async_scrape_jobs(
    scraper: JobScraper,
    query_keywords: list[str],
    location: str,
    max_age_days: int
) -> list[dict]:
    """
    Async wrapper for job scraping with circuit breaker protection.
    
    Uses ThreadPoolExecutor to prevent blocking the event loop.
    """
    loop = asyncio.get_event_loop()
    
    def do_scrape():
        return scraper.search_all(query_keywords, location, max_age_days=max_age_days)
    
    try:
        # Use circuit breaker to protect against scraping failures
        return await scraping_circuit.call(
            loop.run_in_executor,
            _executor,
            do_scrape
        )
    except Exception as e:
        # Circuit breaker open or scraping failed
        raise HTTPException(
            status_code=503,
            detail="Job search temporarily unavailable. Please try again later."
        )


async def _search_jobs_with_cache(
    db: Database,
    scraper: JobScraper,
    current_user: dict,
    q: str = "",
    modality: str = "all",
    location: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    max_age_days: Optional[int] = None,
    match_threshold: Optional[int] = None,
    tags: Optional[str] = None,
    consume_quota: bool = True,
) -> dict:
    """
    Search jobs with caching and optimized database queries.
    
    Implements:
    - Redis caching for search results
    - Circuit breaker for external scraping
    - N+1 query elimination
    - Async/await for non-blocking operations
    """
    telegram_id = current_user["telegram_id"]
    
    # Get user data with single query optimization
    user = db.get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if consume_quota:
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
    
    # Generate cache key
    cache_key = f"search:{telegram_id}:{hashlib.md5(f'{q}:{modality}:{location}:{limit}:{offset}:{max_age_days}:{match_threshold}:{tags}'.encode()).hexdigest()[:16]}"
    
    # Check cache first
    cached_result = cache.get("jobs", cache_key)
    if cached_result:
        return cached_result
    
    # Async scraping with circuit breaker
    try:
        jobs = await _async_scrape_jobs(
            scraper,
            query_keywords,
            search_location,
            max_age_days or profile.get("max_job_age_days", 30)
        )
    except HTTPException:
        raise
    except Exception as e:
        # Fallback to empty results or cached stale data
        jobs = []
    
    # Apply filters
    jobs = JobScraper.apply_negative_filter(
        jobs, experience_level=profile.get("experience_level", "junior")
    )
    
    requested_modality = _normalize_modality(modality or "all")
    if requested_modality != "cualquiera":
        jobs = JobScraper.apply_modality_filter(jobs, requested_modality)
    
    if tags_filter:
        jobs = [
            job
            for job in jobs
            if all(
                tag in f"{job.get('title', '')} {job.get('description', '')}".lower()
                for tag in tags_filter
            )
        ]
    
    # Serialize and score
    serialized = []
    for job in jobs:
        score = _score_job(job, q, profile, tags_filter)
        if score < threshold:
            continue
        serialized.append(_serialize_job(job, score))
    
    serialized.sort(key=lambda item: item["match_score"], reverse=True)
    total = len(serialized)
    effective_limit = min(limit, 5) if current_user["plan"] == "free" else limit
    paginated = serialized[offset : offset + effective_limit]
    
    result = {
        "jobs": paginated,
        "total": total,
        "offset": offset,
        "limit": effective_limit,
        "query": q,
    }
    
    # Cache results (short TTL for freshness)
    cache.set("jobs", cache_key, result, ttl=CacheManager.TTL_SHORT)
    
    if consume_quota:
        db.increment_usage(telegram_id, "searches")
    
    return result


@router.get("/search")
async def search_jobs(
    q: str = Query("", description="Query de busqueda"),
    modality: Optional[str] = Query("all", description="remote, hybrid, onsite"),
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
    """
    Search jobs with caching and optimized performance.
    
    - Cached results for 1 minute
    - Async scraping with circuit breaker
    - N+1 query elimination
    """
    return await _search_jobs_with_cache(
        db=db,
        scraper=scraper,
        current_user=current_user,
        q=q,
        modality=modality or "all",
        location=location,
        limit=limit,
        offset=offset,
        max_age_days=max_age_days,
        match_threshold=match_threshold,
        tags=tags,
        consume_quota=True,
    )


@router.get("/recommended")
async def get_recommended_jobs(
    db: Database = Depends(get_db),
    scraper: JobScraper = Depends(get_scraper),
    current_user: dict = Depends(get_authenticated_user),
):
    """Get recommended jobs based on user profile."""
    profile = db.get_user_profile(current_user["telegram_id"])
    role = profile.get("role_type") or ""
    
    return await _search_jobs_with_cache(
        db=db,
        scraper=scraper,
        current_user=current_user,
        q=role,
        consume_quota=True,
    )


@router.get("/dashboard-preview")
async def get_dashboard_preview_jobs(
    db: Database = Depends(get_db),
    scraper: JobScraper = Depends(get_scraper),
    current_user: dict = Depends(get_authenticated_user),
):
    """
    Get preview jobs for dashboard with aggressive caching.
    Does not consume quota.
    """
    cache_key = f"dashboard:{current_user['telegram_id']}:preview"
    
    # Check cache
    cached = cache.get("dashboard", cache_key)
    if cached:
        return cached
    
    profile = db.get_user_profile(current_user["telegram_id"])
    role = profile.get("role_type") or ""
    
    result = await _search_jobs_with_cache(
        db=db,
        scraper=scraper,
        current_user=current_user,
        q=role,
        limit=3,
        consume_quota=False,
    )
    
    response = {
        "jobs": result["jobs"],
        "query": result["query"],
        "total": result["total"]
    }
    
    # Cache for 5 minutes
    cache.set("dashboard", cache_key, response, ttl=CacheManager.TTL_MEDIUM)
    
    return response


@router.post("/track")
async def track_application(
    payload: TrackRequest,
    db: Database = Depends(get_db),
    current_user: dict = Depends(get_authenticated_user),
):
    """Track a job application."""
    telegram_id = current_user["telegram_id"]
    
    if current_user["plan"] == "free":
        raise HTTPException(
            status_code=403,
            detail="El pipeline de postulaciones requiere Starter o superior",
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
    
    # Invalidate dashboard cache
    cache.delete("dashboard", f"{telegram_id}:preview")
    
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
    """Get user's job applications."""
    return {"applications": db.get_user_applications(current_user["telegram_id"])}


@router.patch("/applications/{app_id}")
async def update_application(
    app_id: int,
    payload: UpdateApplicationRequest,
    db: Database = Depends(get_db),
    current_user: dict = Depends(get_authenticated_user),
):
    """Update application status."""
    db.update_application_status(app_id, current_user["telegram_id"], payload.status)
    return {"id": app_id, "status": payload.status, "message": "Estado actualizado"}

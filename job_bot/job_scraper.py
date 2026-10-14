"""
job_scraper.py - Scrapers para todas las fuentes de empleo

Fuentes implementadas:
  ✅ Remotive API         - API pública gratuita, trabajos remotos IT
  ✅ Arbeitnow API        - API pública gratuita, trabajos remotos/global
  ✅ Jobicy API           - API pública gratuita, trabajos remotos IT
  ✅ Himalayas API        - API pública gratuita, startups & tech remotos
  ✅ Google Jobs           - SerpAPI (100 req gratis/mes — requiere key)
  ✅ Twitter/X             - API v2 (requiere plan Basic $100/mes)
  ✅ Custom RSS            - Cualquier feed RSS que agregues

Fuentes deshabilitadas (sitios bloquean scraping):
  ❌ Indeed Argentina      - RSS eliminado por Indeed (404/403)
  ❌ Computrabajo          - Anti-bot activo, devuelve página genérica
  ❌ Bumeran               - SPA React/Next.js + API bloqueada (403)
  ❌ Tecnoempleo           - Cloudflare protection (403)
"""

import time
import logging
import datetime
import re
import unicodedata
import requests
import feedparser
from bs4 import BeautifulSoup
from email.utils import parsedate_to_datetime
from urllib.parse import parse_qsl, quote_plus, urlencode, urlparse, urlsplit, urlunsplit
from typing import List, Dict, Optional, Tuple

try:
    from job_bot.search_queries import build_search_queries
except ImportError:  # Also support execution from inside the job_bot directory.
    from search_queries import build_search_queries

try:
    from tenacity import retry, stop_after_attempt, wait_exponential
except ImportError:
    # Fallback liviano para tests y entornos mínimos.
    def retry(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

    def stop_after_attempt(*args, **kwargs):
        return None

    def wait_exponential(*args, **kwargs):
        return None

try:
    import config
except ImportError:  # Permite uso como paquete: job_bot.job_scraper
    from job_bot import config

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
    "Accept": "application/json, text/html, */*;q=0.8",
    "Connection": "keep-alive",
}


class JobScraper:
    """Orquesta las búsquedas en todas las fuentes configuradas."""

    def __init__(self):
        self._cache: Dict[str, Tuple[float, object]] = {}
        self._provider_cooldowns: Dict[str, float] = {}
        self.last_search_metrics: List[Dict] = []

    # ----------------------------------------------------------
    # BÚSQUEDA PRINCIPAL
    # ----------------------------------------------------------

    def search_all(
        self,
        keywords: List[str],
        location: str = "Buenos Aires",
        max_age_days: int = 30,
        include_role_taxonomy: bool = True,
    ) -> List[Dict]:
        """
        Busca en todas las fuentes habilitadas para la lista de keywords.
        Retorna una lista de trabajos únicos (deduplicados por URL).
        """
        all_jobs: List[Dict] = []
        self.last_search_metrics = []

        # Get on Board publica un API de búsqueda sin autenticación. Mantener el
        # alcance acotado a Argentina y dos consultas de jornada parcial; su límite
        # de peticiones no está documentado y sus términos permiten throttling.
        if config.SOURCES_ENABLED.get("getonbrd") and include_role_taxonomy:
            for schedule_query in config.GETONBRD_SEARCH_QUERIES:
                self._safe_search(
                    "Get on Board AR",
                    self.search_getonbrd,
                    all_jobs,
                    schedule_query,
                )
                time.sleep(config.REQUEST_DELAY_SECONDS)

        active_keywords = build_search_queries(
            keywords,
            config.GENERAL_SEARCH_KEYWORDS,
            limit=config.MAX_SEARCH_KEYWORDS,
            include_broad=include_role_taxonomy,
        )

        # --- APIs que buscan por query (una request por keyword) ---
        premium_backfill_attempted = False
        for keyword in active_keywords:
            logger.info("🔍 Buscando: '%s'", keyword)
            keyword_start_count = len(all_jobs)

            if config.SOURCES_ENABLED.get("remotive"):
                self._safe_search("Remotive", self.search_remotive, all_jobs, keyword)
                time.sleep(1)

            if config.SOURCES_ENABLED.get("arbeitnow"):
                self._safe_search("Arbeitnow", self.search_arbeitnow, all_jobs, keyword)
                time.sleep(1)

            if config.SOURCES_ENABLED.get("jobicy"):
                self._safe_search("Jobicy", self.search_jobicy, all_jobs, keyword)
                time.sleep(1)

            if config.SOURCES_ENABLED.get("himalayas"):
                self._safe_search("Himalayas", self.search_himalayas, all_jobs, keyword)
                time.sleep(1)

            if config.SOURCES_ENABLED.get("twitter"):
                self._safe_search("Twitter/X", self.search_twitter, all_jobs, keyword)
                time.sleep(config.REQUEST_DELAY_SECONDS)

            # --- Fuentes locales argentinas ---
            if config.SOURCES_ENABLED.get("linkedin_google"):
                self._safe_search("LinkedIn AR (RSS)", self.search_linkedin_google, all_jobs, keyword, location)
                time.sleep(2)

            keyword_results = len(all_jobs) - keyword_start_count
            if (
                not premium_backfill_attempted
                and keyword_results < config.PREMIUM_BACKFILL_MIN_RESULTS
            ):
                self._safe_search(
                    "Premium Backfill",
                    self.search_premium_backfill,
                    all_jobs,
                    keyword,
                    location,
                    config.PREMIUM_BACKFILL_MIN_RESULTS - keyword_results,
                )
                premium_backfill_attempted = True
                time.sleep(config.REQUEST_DELAY_SECONDS)

        unique_jobs = self._dedupe_jobs(all_jobs)

        # Filtrar por ubicación del usuario
        location_filtered = self.apply_location_filter(unique_jobs, location)
        
        # Filtrar ofertas muy viejas (ej: > 45 días)
        date_filtered = self.apply_date_filter(location_filtered, max_days=max_age_days)

        logger.info(
            "📊 Total únicos: %d | Filtro ubicación: %d | Filtro fecha (recientes): %d",
            len(unique_jobs), len(location_filtered), len(date_filtered)
        )
        return date_filtered

    def _safe_search(self, source_name: str, func, results: list, *args):
        """Run one source and retain privacy-safe health metrics for this search."""
        started_at = time.perf_counter()
        try:
            jobs = func(*args)
            results.extend(jobs)
            metric = {
                "source": source_name,
                "status": "ok",
                "jobs_count": len(jobs),
                "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
                "checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
            self.last_search_metrics.append(metric)
            logger.info("  ✅ %s: %d resultado(s)", source_name, len(jobs))
        except Exception as e:
            metric = {
                "source": source_name,
                "status": "error",
                "jobs_count": 0,
                "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
                "error_type": type(e).__name__,
                "checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
            self.last_search_metrics.append(metric)
            logger.error("  ❌ %s falló (%s)", source_name, type(e).__name__)

    def _cache_get(self, key: str):
        cached = self._cache.get(key)
        if not cached:
            return None

        expires_at, value = cached
        if expires_at < time.time():
            self._cache.pop(key, None)
            return None
        return value

    def _cache_set(self, key: str, value, ttl_seconds: int):
        self._cache[key] = (time.time() + ttl_seconds, value)
        return value

    def _normalize_job(self, job: Dict) -> Dict:
        """
        Homogeneiza campos comunes para mejorar deduplicación y UX.
        """
        normalized = dict(job)
        company_domain = self.extract_domain(
            normalized.get("company_domain")
            or normalized.get("company_url")
            or normalized.get("company_website")
            or ""
        )
        if not company_domain:
            company_domain = self.extract_domain(normalized.get("url", ""))
            if company_domain in {"linkedin.com", "google.com", "news.google.com"}:
                company_domain = ""

        normalized["company_domain"] = company_domain
        normalized["title"] = (normalized.get("title") or "Sin título").strip()
        normalized["company"] = (normalized.get("company") or "N/A").strip()
        normalized["url"] = (normalized.get("url") or "").strip()
        normalized["description"] = self._clean_text(normalized.get("description"))
        return normalized

    def _job_fingerprint(self, job: Dict) -> str:
        url = (job.get("url") or "").strip().lower()
        if url:
            return f"url:{self._canonicalize_job_url(url)}"
        title = (job.get("title") or "").strip().lower()
        company = (job.get("company") or "").strip().lower()
        location = (job.get("location") or "").strip().lower()
        return f"meta:{title}|{company}|{location}"

    @staticmethod
    def _canonicalize_job_url(url: str) -> str:
        """Remove common tracking noise while preserving the original apply URL."""
        try:
            parsed = urlsplit(url.strip())
            hostname = (parsed.hostname or "").lower()
            if hostname.startswith("www."):
                hostname = hostname[4:]
            port = parsed.port
            netloc = hostname
            if port and not ((parsed.scheme.lower() == "https" and port == 443) or (parsed.scheme.lower() == "http" and port == 80)):
                netloc = f"{hostname}:{port}"
            tracking_names = {"ref", "source", "gclid", "fbclid", "mc_cid", "mc_eid"}
            query = [
                (key, value)
                for key, value in parse_qsl(parsed.query, keep_blank_values=True)
                if not key.lower().startswith("utm_") and key.lower() not in tracking_names
            ]
            query.sort()
            path = parsed.path.rstrip("/") or "/"
            scheme = parsed.scheme.lower() or "https"
            return urlunsplit((scheme, netloc, path, urlencode(query, doseq=True), ""))
        except (TypeError, ValueError):
            return url

    def _dedupe_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """
        Deduplica por URL si existe; si no, por título+empresa+ubicación.
        """
        seen: Dict[str, int] = {}
        unique_jobs: List[Dict] = []
        for raw_job in jobs:
            job = self._normalize_job(raw_job)
            fingerprint = self._job_fingerprint(job)
            sources = job.get("sources") or ([job.get("source")] if job.get("source") else [])
            if isinstance(sources, str):
                sources = [sources]
            job["sources"] = list(dict.fromkeys(source for source in sources if source))

            if fingerprint in seen:
                existing = unique_jobs[seen[fingerprint]]
                existing["sources"] = list(
                    dict.fromkeys(existing["sources"] + job["sources"])
                )
                continue
            seen[fingerprint] = len(unique_jobs)
            unique_jobs.append(job)
        return unique_jobs

    def _provider_ready(self, provider_name: str) -> bool:
        cooldown_until = self._provider_cooldowns.get(provider_name, 0)
        return cooldown_until <= time.time()

    def _trip_provider(self, provider_name: str):
        self._provider_cooldowns[provider_name] = (
            time.time() + config.PROVIDER_COOLDOWN_SECONDS
        )

    @staticmethod
    def extract_domain(value: str) -> str:
        """Extrae un dominio limpio desde un dominio suelto o URL."""
        if not value:
            return ""

        candidate = value.strip()
        if "://" not in candidate:
            candidate = f"https://{candidate}"

        parsed = urlparse(candidate)
        netloc = (parsed.netloc or parsed.path or "").strip().lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc.split("/")[0]

    @staticmethod
    def _clean_text(value: Optional[str], limit: int = 300) -> str:
        text = (value or "").strip()
        return text[:limit]

    def _rapidapi_headers(self, host: str) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "X-RapidAPI-Key": config.RAPIDAPI_KEY,
            "X-RapidAPI-Host": host,
        }

    def _requests_get_json(self, url: str, *, params: Optional[Dict] = None, headers: Optional[Dict] = None):
        response = requests.get(
            url,
            params=params,
            headers=headers or HEADERS,
            timeout=config.REQUEST_TIMEOUT,
        )
        if response.status_code == 429:
            raise ValueError("Quota/rate limit alcanzado")
        response.raise_for_status()
        return response.json()

    def search_premium_backfill(self, query: str, location: str, missing_results: int = 3) -> List[Dict]:
        """
        Usa proveedores premium sólo si las fuentes gratis no alcanzan.
        Orden: Active Jobs DB -> Google Jobs (SerpAPI) -> JSearch/LinkedIn robust.
        """
        jobs: List[Dict] = []

        premium_calls = [
            ("active_jobs_db", self.search_active_jobs_db, (query, location)),
            ("serpapi_google", self.search_google_jobs, (query, location)),
            ("linkedin_robust", self.search_linkedin_robust, (query, location, False)),
        ]

        for provider_name, provider_fn, args in premium_calls:
            if len(jobs) >= max(missing_results, 1):
                break
            if not self._provider_ready(provider_name):
                continue
            try:
                provider_jobs = provider_fn(*args)
                jobs.extend(provider_jobs)
            except Exception as e:
                logger.warning("Provider premium %s no disponible: %s", provider_name, e)
                self._trip_provider(provider_name)

        return jobs[: config.MAX_RESULTS_PER_SOURCE]

    def search_getonbrd(self, query: str) -> List[Dict]:
        """Search published Argentina listings through Get on Board's public API."""
        data = self._requests_get_json(
            "https://www.getonbrd.com/api/v0/search/jobs",
            params={
                "query": query,
                "country_code": "ar",
                "page": 1,
                "per_page": config.MAX_RESULTS_PER_SOURCE,
                "lang": "en",
                "expand": '["company"]',
            },
        )

        items = data.get("data", []) if isinstance(data, dict) else []
        jobs: List[Dict] = []
        for item in items[: config.MAX_RESULTS_PER_SOURCE]:
            attributes = item.get("attributes") or {}
            company = attributes.get("company") or {}
            company_data = company.get("data") or company
            company_attributes = company_data.get("attributes") or company_data
            company_name = company_attributes.get("name") or company_data.get("id") or "N/A"

            country_names = attributes.get("countries") or []
            remote_zone = attributes.get("remote_zone")
            is_remote = bool(attributes.get("remote"))
            location_parts = list(country_names)
            if remote_zone and remote_zone not in location_parts:
                location_parts.append(remote_zone)
            if is_remote:
                location_parts.append("Remoto")
            location = " · ".join(str(part) for part in location_parts if part) or "Argentina"

            description_parts = (
                attributes.get("description_headline"),
                attributes.get("description"),
                attributes.get("functions"),
                attributes.get("projects"),
                attributes.get("desirable"),
            )
            description = BeautifulSoup(
                " ".join(str(part) for part in description_parts if part),
                "html.parser",
            ).get_text(separator=" ").strip()

            published_at = attributes.get("published_at")
            try:
                published_date = time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(published_at))
                )
            except (TypeError, ValueError, OverflowError):
                published_date = ""

            modality = attributes.get("modality") or {}
            modality_data = modality.get("data") or {}
            links = item.get("links") or {}
            jobs.append(
                {
                    "title": attributes.get("title") or "Sin título",
                    "company": company_name,
                    "location": location,
                    "url": links.get("public_url") or item.get("url") or "",
                    "description": description[:1200],
                    "source": "Get on Board",
                    "date": published_date,
                    "employment_type": modality_data.get("type") or "",
                    "salary_min": attributes.get("min_salary"),
                    "salary_max": attributes.get("max_salary"),
                    "salary_currency": None,
                }
            )

        return jobs

    # ----------------------------------------------------------
    # 1. REMOTIVE — API PÚBLICA GRATUITA
    # ----------------------------------------------------------

    def search_remotive(self, query: str) -> List[Dict]:
        """
        Remotive API — trabajos remotos IT.
        API pública sin key: https://remotive.com/api/remote-jobs
        """
        url = "https://remotive.com/api/remote-jobs"
        params = {
            "search": query,
            "limit": config.MAX_RESULTS_PER_SOURCE,
        }

        try:
            response = requests.get(url, params=params, headers=HEADERS, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            logger.error("Remotive API error: %s", e)
            return []

        jobs: List[Dict] = []
        for item in data.get("jobs", [])[:config.MAX_RESULTS_PER_SOURCE]:
            # Limpiar HTML de la descripción
            raw_desc = item.get("description", "")
            description = BeautifulSoup(raw_desc, "html.parser").get_text(separator=" ").strip()

            jobs.append({
                "title":       item.get("title", "Sin título").strip(),
                "company":     item.get("company_name", "N/A"),
                "location":    item.get("candidate_required_location", "🌐 Remoto"),
                "url":         item.get("url", ""),
                "description": description[:300],
                "source":      "Remotive",
                "date":        item.get("publication_date", ""),
            })

        return jobs

    # ----------------------------------------------------------
    # 2. ARBEITNOW — API PÚBLICA GRATUITA
    # ----------------------------------------------------------

    def search_arbeitnow(self, query: str) -> List[Dict]:
        """
        Arbeitnow API — trabajos remotos/globales.
        API pública sin key: https://www.arbeitnow.com/api/job-board-api
        """
        url = "https://www.arbeitnow.com/api/job-board-api"
        params = {"search": query}

        try:
            response = requests.get(url, params=params, headers=HEADERS, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            logger.error("Arbeitnow API error: %s", e)
            return []

        jobs: List[Dict] = []
        for item in data.get("data", [])[:config.MAX_RESULTS_PER_SOURCE]:
            # Limpiar HTML
            raw_desc = item.get("description", "")
            description = BeautifulSoup(raw_desc, "html.parser").get_text(separator=" ").strip()

            tags = item.get("tags", [])
            tags_str = ", ".join(tags[:5]) if tags else ""

            jobs.append({
                "title":       item.get("title", "Sin título").strip(),
                "company":     item.get("company_name", "N/A"),
                "location":    item.get("location", "🌐 Remoto"),
                "url":         item.get("url", ""),
                "description": (description[:250] + f" [{tags_str}]") if tags_str else description[:300],
                "source":      "Arbeitnow",
                "date":        item.get("created_at", ""),
            })

        return jobs

    # ----------------------------------------------------------
    # 3. JOBICY — API PÚBLICA GRATUITA
    # ----------------------------------------------------------

    def search_jobicy(self, query: str) -> List[Dict]:
        """
        Jobicy API — trabajos remotos IT.
        API pública sin key: https://jobicy.com/api/v2/remote-jobs
        Docs: https://jobicy.com/jobs-rss-feed
        """
        url = "https://jobicy.com/api/v2/remote-jobs"
        params = {
            "count": config.MAX_RESULTS_PER_SOURCE,
            "tag": query,
        }

        try:
            response = requests.get(url, params=params, headers=HEADERS, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            # Esta API a veces devuelve 400 para ciertos tags; lo consideramos un warning
            # porque el bot sigue funcionando con el resto de las fuentes.
            logger.warning("Jobicy API error: %s", e)
            return []

        jobs: List[Dict] = []
        for item in data.get("jobs", [])[:config.MAX_RESULTS_PER_SOURCE]:
            # Limpiar HTML entities
            title = item.get("jobTitle", "Sin título")
            if "<" in title:
                title = BeautifulSoup(title, "html.parser").get_text().strip()
            else:
                # Decode HTML entities without BeautifulSoup
                import html
                title = html.unescape(title).strip()

            raw_desc = item.get("jobExcerpt", "")
            description = BeautifulSoup(raw_desc, "html.parser").get_text(separator=" ").strip()

            salary_min = item.get("annualSalaryMin", "")
            salary_max = item.get("annualSalaryMax", "")
            salary_cur = item.get("salaryCurrency", "")
            salary = ""
            if salary_min and salary_max:
                salary = f" 💰 {salary_cur}{salary_min}-{salary_max}"

            jobs.append({
                "title":       title,
                "company":     item.get("companyName", "N/A"),
                "location":    item.get("jobGeo", "🌐 Remoto"),
                "url":         item.get("url", ""),
                "description": (description[:280] + salary) if salary else description[:300],
                "source":      "Jobicy",
                "date":        item.get("pubDate", ""),
            })

        return jobs

    # ----------------------------------------------------------
    # 4. HIMALAYAS — API PÚBLICA GRATUITA
    # ----------------------------------------------------------

    def search_himalayas(self, query: str) -> List[Dict]:
        """
        Himalayas API — Tech & Startup remote jobs.
        API pública sin key: https://himalayas.app/jobs/api
        """
        url = "https://himalayas.app/jobs/api"
        # The API doesn't have a direct search query param in its free tier,
        # but supports limit and offset. We fetch the latest and filter.
        params = {"limit": 50} 

        try:
            response = requests.get(url, params=params, headers=HEADERS, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            logger.error("Himalayas API error: %s", e)
            return []

        jobs: List[Dict] = []
        query_lower = query.lower()
        items = data.get("jobs", [])
        
        # Filtro manual porque la API no tiene ?search=
        matched_items = [
            item for item in items 
            if query_lower in item.get("title", "").lower() or query_lower in item.get("description", "").lower()
        ][:config.MAX_RESULTS_PER_SOURCE]

        for item in matched_items:
            # Limpiar HTML
            raw_desc = item.get("description", "")
            description = BeautifulSoup(raw_desc, "html.parser").get_text(separator=" ").strip()

            jobs.append({
                "title":       item.get("title", "Sin título").strip(),
                "company":     item.get("companyName", "N/A"),
                "location":    item.get("locationRestrictions", ["🌐 Remoto"])[0] if item.get("locationRestrictions") else "🌐 Remoto",
                "url":         item.get("applicationLink", "") or item.get("himalayasCompanyProfileLink", ""),
                "description": description[:300],
                "source":      "Himalayas",
                "date":        item.get("pubDate", ""),
            })

        return jobs

    # ----------------------------------------------------------
    # 4. GOOGLE JOBS via SerpAPI — 100 req/mes GRATIS
    # ----------------------------------------------------------

    def search_google_jobs(self, query: str, location: str = "Buenos Aires") -> List[Dict]:
        """
        Google Jobs mediante SerpAPI.
        100 búsquedas gratuitas por mes. Registrate en https://serpapi.com
        """
        if not config.SERPAPI_KEY:
            logger.warning("SerpAPI key no configurada. Saltando Google Jobs.")
            return []

        params = {
            "engine":  "google_jobs",
            "q":       f"{query} {location}",
            "api_key": config.SERPAPI_KEY,
            "hl":      "es",
            "gl":      "ar",
            "num":     str(config.MAX_RESULTS_PER_SOURCE),
        }

        try:
            response = requests.get(
                "https://serpapi.com/search",
                params=params,
                timeout=config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            logger.error("SerpAPI error: %s", e)
            return []

        if "error" in data:
            logger.error("SerpAPI devolvió error: %s", data["error"])
            return []

        jobs: List[Dict] = []
        for item in data.get("jobs_results", [])[:config.MAX_RESULTS_PER_SOURCE]:
            apply_link = ""
            apply_options = item.get("apply_options", [])
            if apply_options:
                apply_link = apply_options[0].get("link", "")
            if not apply_link:
                apply_link = item.get("share_link",
                    f"https://www.google.com/search?q={quote_plus(item.get('title', ''))}")

            jobs.append({
                "title":       item.get("title", "Sin título"),
                "company":     item.get("company_name", "N/A"),
                "location":    item.get("location", location),
                "url":         apply_link,
                "description": (item.get("description") or "")[:300],
                "source":      "Google Jobs",
                "date":        item.get("detected_extensions", {}).get("posted_at", ""),
            })

        return jobs

    def search_active_jobs_db(self, query: str, location: str = "Buenos Aires") -> List[Dict]:
        """
        Busca en Active Jobs DB vía RapidAPI.
        Se usa como backfill premium cuando las fuentes gratis quedan cortas.
        """
        if not config.RAPIDAPI_KEY:
            raise ValueError("RAPIDAPI_KEY no configurada")

        cache_key = f"active_jobs:{query}:{location}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        host = config.RAPIDAPI_ACTIVE_JOBS_HOST
        url = f"https://{host}/active-ats-1h"
        params = {
            "offset": "0",
            "title_filter": f"\"{query}\"",
            "location_filter": f"\"{location}\"",
            "description_type": "text",
        }

        data = self._requests_get_json(
            url,
            params=params,
            headers=self._rapidapi_headers(host),
        )

        raw_items = data if isinstance(data, list) else data.get("jobs", [])
        jobs: List[Dict] = []
        for item in raw_items[: config.MAX_RESULTS_PER_SOURCE]:
            apply_url = (
                item.get("job_url")
                or item.get("apply_url")
                or item.get("url")
                or ""
            )
            company_site = item.get("company_website") or item.get("company_url") or ""
            jobs.append({
                "id": item.get("id") or item.get("job_id") or apply_url,
                "title": item.get("title", "Sin título").strip(),
                "company": item.get("organization") or item.get("company") or "N/A",
                "location": item.get("locations_derived", [location])[0] if item.get("locations_derived") else item.get("location", location),
                "url": apply_url,
                "description": self._clean_text(item.get("description") or item.get("description_text")),
                "source": "Active Jobs DB",
                "date": item.get("date_posted") or item.get("created_at", ""),
                "company_domain": self.extract_domain(company_site),
                "provider": "active_jobs_db",
            })

        if not jobs:
            raise ValueError("Active Jobs DB devolvió 0 resultados")

        return self._cache_set(cache_key, jobs, config.PROVIDER_CACHE_TTL_SECONDS)

    # ----------------------------------------------------------
    # 5. TWITTER/X API v2
    # ⚠️  Requiere plan Basic ($100/mes). El plan Free NO permite buscar tweets.
    # ----------------------------------------------------------

    def search_twitter(self, query: str) -> List[Dict]:
        """
        Twitter/X API v2 — búsqueda de tweets recientes.
        IMPORTANTE: Requiere plan Basic ($100/mes). El Free tier no tiene búsqueda.
        """
        if not config.TWITTER_BEARER_TOKEN:
            return []

        search_q = (
            f"({query}) "
            f"(empleo OR trabajo OR oportunidad OR hiring OR oferta OR busco) "
            f"lang:es "
            f"-is:retweet -is:reply"
        )

        headers = {
            "Authorization": f"Bearer {config.TWITTER_BEARER_TOKEN}",
            "User-Agent": "v2RecentSearchPython",
        }
        params = {
            "query":        search_q,
            "max_results":  "10",
            "tweet.fields": "created_at,author_id,text,entities",
            "expansions":   "author_id",
            "user.fields":  "name,username,verified",
        }

        try:
            response = requests.get(
                "https://api.twitter.com/2/tweets/search/recent",
                headers=headers,
                params=params,
                timeout=config.REQUEST_TIMEOUT,
            )

            if response.status_code == 403:
                logger.warning(
                    "Twitter API 403: El plan gratuito no soporta búsqueda. "
                    "Necesitás el plan Basic ($100/mes)."
                )
                return []

            response.raise_for_status()
            data = response.json()

        except requests.RequestException as e:
            logger.error("Twitter API error: %s", e)
            return []

        users_map: Dict[str, Dict] = {}
        for user in data.get("includes", {}).get("users", []):
            users_map[user["id"]] = user

        jobs: List[Dict] = []
        for tweet in data.get("data", []):
            author = users_map.get(tweet.get("author_id", ""), {})
            username = author.get("username", "unknown")
            tweet_url = f"https://twitter.com/{username}/status/{tweet['id']}"
            text = tweet.get("text", "")

            jobs.append({
                "title":       (text[:80] + "...") if len(text) > 80 else text,
                "company":     author.get("name", "Usuario de Twitter"),
                "location":    "Twitter/X — posiblemente remoto",
                "url":         tweet_url,
                "description": text[:300],
                "source":      "Twitter/X",
                "date":        tweet.get("created_at", ""),
            })

        return jobs

    # ----------------------------------------------------------
    # 6. CUSTOM RSS — Cualquier feed RSS que el usuario agregue
    # ----------------------------------------------------------

    def search_custom_rss(self, feed_url: str, feed_name: str) -> List[Dict]:
        """
        Parsea cualquier RSS feed configurado por el usuario.
        Ideal para feeds de empresas específicas.
        """
        try:
            feed = feedparser.parse(feed_url)
        except Exception as e:
            logger.error("Custom RSS '%s' error: %s", feed_name, e)
            return []

        jobs: List[Dict] = []
        for entry in feed.entries[:config.MAX_RESULTS_PER_SOURCE]:
            raw_desc = entry.get("summary", entry.get("description", ""))
            description = BeautifulSoup(raw_desc, "html.parser").get_text(separator=" ").strip()

            jobs.append({
                "title":       entry.get("title", "Sin título").strip(),
                "company":     entry.get("author", feed_name),
                "location":    "N/A",
                "url":         entry.get("link", ""),
                "description": description[:300],
                "source":      f"RSS: {feed_name}",
                "date":        entry.get("published", ""),
            })

        return jobs

    # ----------------------------------------------------------
    # ESTRATEGIA DE FALLBACK / ROTACIÓN PARA LINKEDIN
    # ----------------------------------------------------------

    def search_linkedin_robust(self, query: str, location: str = "Buenos Aires", allow_rss_fallback: bool = True) -> List[Dict]:
        """
        Enrutador profesional que previene caídas. Intenta múltiples proveedores.
        Si la Opción 1 falla, pasa a la Opción 2, y así sucesivamente.
        """
        logger.info("🛡️ Iniciando búsqueda robusta de LinkedIn para: '%s' en '%s'", query, location)
        
        # Estrategia 1: API comercial (ej. RapidAPI JSearch / Proxycurl)
        try:
            return self._fetch_linkedin_via_rapidapi(query, location)
        except Exception as e:
            logger.debug("Fallback 1 (Comercial API) omitido o falló: %s", e)

        # Estrategia 2: SerpAPI Google Search
        try:
            return self._fetch_linkedin_via_serpapi_search(query, location)
        except Exception as e:
            logger.debug("Fallback 2 (SerpAPI) omitido o falló: %s", e)

        # Estrategia 3: Google News RSS (Gratis, con retries vía Tenacity)
        if allow_rss_fallback:
            try:
                return self._fetch_linkedin_via_google_rss_retry(query, location)
            except Exception as e:
                logger.error("❌ Todos los fallbacks de LinkedIn fallaron. Último error: %s", e)
                return []

        return []

    def _fetch_linkedin_via_rapidapi(self, query: str, location: str) -> List[Dict]:
        """
        Utiliza "JSearch" o similar en RapidAPI. (Plan Free: ~100-200 mensuales)
        """
        if not getattr(config, 'RAPIDAPI_KEY', None):
            raise ValueError("RAPIDAPI_KEY no configurada en las variables de entorno.")

        host = config.RAPIDAPI_JSEARCH_HOST
        url = f"https://{host}/search"
        querystring = {
            "query": f"{query} en {location} LinkedIn",
            "page": "1",
            "num_pages": "1",
            "date_posted": "month",
            "language": "es"
        }
        headers = self._rapidapi_headers(host)

        response = requests.get(url, headers=headers, params=querystring, timeout=config.REQUEST_TIMEOUT)
        if response.status_code == 429:
            raise ValueError("Límite de RapidAPI alcanzado (429 Too Many Requests)")
        response.raise_for_status()
        
        data = response.json()
        jobs = []
        for item in data.get("data", [])[:config.MAX_RESULTS_PER_SOURCE]:
            jobs.append({
                "id": item.get("job_id", ""),
                "title": item.get("job_title", "Sin título"),
                "company": item.get("employer_name", "Ver empresa"),
                "location": item.get("job_city", "") + " " + item.get("job_country", location),
                "url": item.get("job_apply_link", ""),
                "description": item.get("job_description", "")[:300],
                "source": "LinkedIn API (Rapid)",
                "date": item.get("job_posted_at_datetime_utc", ""),
                "company_domain": self.extract_domain(item.get("employer_website", "")),
                "provider": "jsearch",
            })
            
        if not jobs:
            raise ValueError("RapidAPI devolvió 0 resultados")
            
        return jobs

    def _fetch_linkedin_via_serpapi_search(self, query: str, location: str) -> List[Dict]:
        """
        Raspa LinkedIn a través del buscador clásico de Google vía SerpAPI.
        (Usa cuota de tus 100/mes de SerpAPI)
        """
        if not getattr(config, 'SERPAPI_KEY', None):
            raise ValueError("SERPAPI_KEY no configurada")

        search_q = f"site:linkedin.com/jobs/view {query} {location}"
        params = {
            "engine": "google",
            "q": search_q,
            "api_key": config.SERPAPI_KEY,
            "hl": "es",
            "gl": "ar"
        }

        response = requests.get("https://serpapi.com/search", params=params, timeout=config.REQUEST_TIMEOUT)
        if response.status_code != 200 or "error" in response.json():
            raise ValueError("SerpAPI falló o se quedó sin créditos.")
            
        data = response.json()
        jobs = []
        for item in data.get("organic_results", [])[:config.MAX_RESULTS_PER_SOURCE]:
            title = item.get("title", "").replace(" - LinkedIn", "")
            snippet = item.get("snippet", "")
            
            jobs.append({
                "title": title,
                "company": "LinkedIn", # Google Search no siempre separa bien la empresa aquí
                "location": location,
                "url": item.get("link", ""),
                "description": snippet,
                "source": "LinkedIn AR (SerpAPI)",
                "date": "",
                "provider": "serpapi_linkedin",
            })
            
        if not jobs:
            raise ValueError("SerpAPI devolvió 0 resultados")
            
        return jobs

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch_linkedin_via_google_rss_retry(self, query: str, location: str) -> List[Dict]:
        """Envuelve Google News RSS con reintentos para evadir baneos temporales."""
        logger.info("  Intentando LinkedIn vía Google News RSS (con posibles reintentos)...")
        jobs = self.search_linkedin_google(query, location)
        if not jobs:
            # Forzamos un error si vino vacío para que el @retry actúe saltando al siguiente intento
            raise ValueError("Google RSS devolvió 0 resultados o fuimos bloqueados temporalmente.")
        return jobs

    # ----------------------------------------------------------
    # 7. LINKEDIN JOBS via GOOGLE NEWS RSS — ARGENTINA LOCAL (Implementación base)
    # ----------------------------------------------------------

    def search_linkedin_google(self, query: str, location: str = "Buenos Aires") -> List[Dict]:
        """
        Busca ofertas de LinkedIn Argentina usando Google News RSS.
        No requiere API key. Devuelve ofertas reales de LinkedIn
        publicadas en Argentina y alrededores.
        """
        import re

        search_q = f"site:linkedin.com/jobs {query} {location}"
        url = (
            f"https://news.google.com/rss/search"
            f"?q={quote_plus(search_q)}"
            f"&hl=es-419&gl=AR&ceid=AR:es-419"
        )

        try:
            feed = feedparser.parse(url)
        except Exception as e:
            logger.error("LinkedIn/Google RSS error: %s", e)
            return []

        jobs: List[Dict] = []
        for entry in feed.entries[:config.MAX_RESULTS_PER_SOURCE]:
            title_raw = entry.get("title", "")

            # El título viene como "Empresa busca Puesto en Ciudad - LinkedIn"
            # Limpiar el sufijo " - LinkedIn"
            title = re.sub(r"\s*-\s*LinkedIn\s*$", "", title_raw).strip()
            if not title or len(title) < 5:
                continue

            # Saltar páginas de búsqueda de LinkedIn ("777 empleos de X en Argentina")
            if re.match(r"^\d+\s+empleos?\s+de\s+", title):
                continue

            # Extraer empresa si el formato es "Empresa busca ... para el cargo de ..."
            company = "Ver en LinkedIn"
            if " busca personal para " in title:
                parts = title.split(" busca personal para ")
                company = parts[0].strip()
                title = parts[1].strip() if len(parts) > 1 else title
                # Limpiar "el cargo de " del título
                title = re.sub(r"^el cargo de\s+", "", title)
                # Limpiar " en Ciudad y alrededores"
                title = re.sub(r"\s+en\s+[\w\s,]+y alrededores$", "", title)
            elif " | " in title:
                parts = title.split(" | ")
                if len(parts) >= 2:
                    title = parts[0].strip()
                    company = parts[1].strip()

            # El link de Google News es un redirect, pero funciona
            job_url = entry.get("link", "")

            jobs.append({
                "title":       title,
                "company":     company,
                "location":    location,
                "url":         job_url,
                "description": "",
                "source":      "LinkedIn AR",
                "date":        entry.get("published", ""),
                "provider":    "linkedin_google_rss",
            })

        return jobs

    def get_job_details(self, job_id: str, country: str = "us") -> Dict:
        """Obtiene detalle extendido de un job vía JSearch Mega."""
        if not job_id:
            raise ValueError("job_id requerido")
        if not config.RAPIDAPI_KEY:
            raise ValueError("RAPIDAPI_KEY no configurada")

        cache_key = f"job_details:{job_id}:{country}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        host = config.RAPIDAPI_JSEARCH_MEGA_HOST
        url = f"https://{host}/job-details"
        params = {
            "job_id": job_id,
            "country": country,
        }
        data = self._requests_get_json(
            url,
            params=params,
            headers=self._rapidapi_headers(host),
        )
        return self._cache_set(cache_key, data, config.PROVIDER_CACHE_TTL_SECONDS)

    def enrich_company_by_domain(self, domain_or_url: str) -> Dict:
        """Enriquece una empresa por dominio usando linkedin-data-api."""
        domain = self.extract_domain(domain_or_url)
        if not domain:
            raise ValueError("No pude extraer un dominio válido")

        cache_key = f"company:{domain}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        if not config.RAPIDAPI_KEY:
            raise ValueError("RAPIDAPI_KEY no configurada")

        host = config.RAPIDAPI_LINKEDIN_DATA_HOST
        url = f"https://{host}/get-company-by-domain"
        data = self._requests_get_json(
            url,
            params={"domain": domain},
            headers=self._rapidapi_headers(host),
        )

        normalized = {
            "domain": domain,
            "name": data.get("name") or data.get("companyName") or domain,
            "headline": data.get("headline") or data.get("tagline") or "",
            "description": self._clean_text(data.get("description") or data.get("summary"), 500),
            "industry": data.get("industry") or data.get("industries", ""),
            "size": data.get("companySize") or data.get("staffCount") or "",
            "website": data.get("website") or data.get("companyWebsite") or "",
            "linkedin_url": data.get("linkedinUrl") or data.get("url") or "",
            "location": data.get("headquarters") or data.get("location") or "",
            "founded": data.get("foundedOn") or data.get("founded") or "",
            "logo": data.get("logo") or data.get("logoUrl") or "",
            "raw": data,
        }
        return self._cache_set(cache_key, normalized, config.COMPANY_CACHE_TTL_SECONDS)

    # ----------------------------------------------------------
    # FILTRO POR UBICACIÓN DEL USUARIO
    # ----------------------------------------------------------

    @staticmethod
    def apply_location_filter(jobs: List[Dict], user_location: str) -> List[Dict]:
        """
        Filtra trabajos para mostrar solo los relevantes a la ubicación del usuario.
        Acepta:
          - Trabajos en la misma región/país del usuario
          - Trabajos remotos abiertos globalmente (Anywhere, Worldwide, etc.)
          - Trabajos que mencionan LATAM, Latin America, South America
        Rechaza:
          - Trabajos en países/ciudades específicas que no coinciden
        """
        def normalize(value: str) -> str:
            decomposed = unicodedata.normalize("NFKD", value.lower())
            return "".join(char for char in decomposed if not unicodedata.combining(char))

        def has_phrase(text: str, phrase: str) -> bool:
            normalized_phrase = normalize(phrase.strip())
            return bool(
                normalized_phrase
                and re.search(r"(?<![a-z0-9])" + re.escape(normalized_phrase) + r"(?![a-z0-9])", text)
            )

        user_loc = normalize(user_location or "")
        user_terms = set(user_loc.split())
        if any(term in {"argentina", "buenos", "aires", "caba"} for term in user_terms):
            user_terms.update(config.LOCATION_VARIANTS)
        explicitly_global_terms = config.GLOBAL_LOCATION_TERMS - {
            "remote", "remoto", "international", "americas", "america"
        }
        remote_terms = {"remote", "remoto", "work from anywhere", "work from home", "wfh"}

        filtered = []
        for job in jobs:
            job_loc = normalize(str(job.get("location") or ""))

            # Unknown and globally remote listings stay visible, but are not
            # presented as confirmed Argentina-eligible opportunities.
            if not job_loc or job_loc == "n/a":
                job["location_match"] = "unknown"
                filtered.append(job)
                continue

            if any(has_phrase(job_loc, term) for term in user_terms):
                job["location_match"] = "eligible"
                filtered.append(job)
                continue

            if any(has_phrase(job_loc, term) for term in explicitly_global_terms):
                job["location_match"] = "eligible"
                filtered.append(job)
                continue

            if any(has_phrase(job_loc, term) for term in remote_terms):
                job["location_match"] = "unknown"
                filtered.append(job)
                continue

            logger.debug("Filtrado por ubicación: '%s' (job: %s)", job_loc, job.get("title", ""))

        return filtered

    # ----------------------------------------------------------
    # FILTRO POR MODALIDAD (Remoto, Híbrido, Presencial)
    # ----------------------------------------------------------

    @staticmethod
    def apply_modality_filter(jobs: List[Dict], modality: str) -> List[Dict]:
        """
        Filtra trabajos según su modalidad. Por defecto, 'cualquiera' no filtra nada.
        Usa heurísticas en location/título/descripción para determinarlo.
        """
        modality = modality.lower()
        if modality not in ["remoto", "híbrido", "hibrido", "presencial"]:
            return jobs

        filtered = []
        for job in jobs:
            text = f"{job.get('title','')} {job.get('location','')} {job.get('description','')}".lower()
            
            # Detectar la modalidad del trabajo actual
            is_remote = any(m in text for m in ["remoto", "remote", "anywhere", "work from home", "wfh"])
            is_hybrid = any(m in text for m in ["híbrido", "hibrido", "hybrid"])
            # Si no es remoto ni híbrido, asumimos presencial/onsite
            is_onsite = ("onsite" in text or "on-site" in text or "presencial" in text) or (not is_remote and not is_hybrid)

            if modality == "remoto" and (is_remote or job.get("source") in ["Remotive", "Arbeitnow", "Jobicy", "Himalayas"]):
                filtered.append(job)
            elif modality in ["híbrido", "hibrido"] and (is_hybrid or (is_remote and is_onsite)):
                filtered.append(job)
            elif modality == "presencial" and is_onsite and not is_remote and not is_hybrid:
                filtered.append(job)
            elif is_remote and modality == "remoto": # Fallback
                filtered.append(job)
                
        # Mostrar el total que quedó después del filtrado
        logger.debug("Filtrado por modalidad '%s': quedaron %d de %d", modality, len(filtered), len(jobs))
        return filtered

    @staticmethod
    def apply_schedule_filter(jobs: List[Dict], schedule: str) -> List[Dict]:
        """
        Filtra trabajos según jornada: full-time, part-time o cualquiera.
        """
        normalized = (schedule or "cualquiera").strip().lower()
        if normalized not in ["full_time", "part_time"]:
            return jobs

        filtered = []
        for job in jobs:
            inferred_schedule = JobScraper.infer_job_schedule(job)

            if normalized == "part_time" and inferred_schedule == "part_time":
                filtered.append(job)
            elif normalized == "full_time" and inferred_schedule == "full_time":
                filtered.append(job)

        logger.debug(
            "Filtrado por jornada '%s': quedaron %d de %d",
            normalized,
            len(filtered),
            len(jobs),
        )
        return filtered

    @staticmethod
    def infer_job_schedule(job: Dict) -> str:
        """Infer a listing's stated schedule without treating unknown as full-time."""
        text = " ".join(
            str(job.get(field) or "")
            for field in ("title", "location", "description", "employment_type", "schedule")
        ).lower().replace("_", " ")

        part_time_terms = (
            "part time",
            "part-time",
            "parttime",
            "media jornada",
            "half time",
            "jornada reducida",
        )
        full_time_terms = (
            "full time",
            "full-time",
            "fulltime",
            "tiempo completo",
            "jornada completa",
        )

        if any(term in text for term in part_time_terms):
            return "part_time"
        if any(term in text for term in full_time_terms):
            return "full_time"
        return "unknown"

    @staticmethod
    def prioritize_part_time(jobs: List[Dict]) -> List[Dict]:
        """Rank explicit part-time listings first, then rank each group by match."""
        return sorted(
            jobs,
            key=lambda job: (
                JobScraper.infer_job_schedule(job) != "part_time",
                -int(job.get("match_score") or 0),
            ),
        )

    @staticmethod
    def apply_profile_relevance_filter(
        jobs: List[Dict], role_type: str = "", technologies: str = ""
    ) -> List[Dict]:
        """
        Filtra resultados demasiado genéricos usando rol y stack del usuario.
        """
        role_terms = [
            part.strip().lower()
            for part in role_type.replace("/", ",").split(",")
            if part.strip()
        ]
        tech_terms = [part.strip().lower() for part in technologies.split(",") if part.strip()]

        if not role_terms and not tech_terms:
            return jobs

        filtered = []
        for job in jobs:
            haystack = f"{job.get('title','')} {job.get('description','')} {job.get('company','')}".lower()
            role_hits = sum(1 for term in role_terms if term in haystack)
            tech_hits = sum(1 for term in tech_terms if term in haystack)

            if role_terms and tech_terms:
                if role_hits >= 1 or tech_hits >= 2:
                    filtered.append(job)
            elif role_terms and role_hits >= 1:
                filtered.append(job)
            elif tech_terms and tech_hits >= 1:
                filtered.append(job)

        logger.debug(
            "Filtrado por perfil (roles=%s techs=%s): quedaron %d de %d",
            role_terms,
            tech_terms,
            len(filtered),
            len(jobs),
        )
        return filtered

    @staticmethod
    def annotate_profile_relevance(
        jobs: List[Dict], role_type: str = "", technologies: str = ""
    ) -> List[Dict]:
        """Keep broad-search results visible while labeling profile overlap."""
        role_terms = [
            part.strip().lower()
            for part in (role_type or "").replace("/", ",").split(",")
            if part.strip()
        ]
        tech_terms = [
            part.strip().lower()
            for part in (technologies or "").split(",")
            if part.strip()
        ]
        annotated = []
        for original in jobs:
            job = dict(original)
            haystack = f"{job.get('title', '')} {job.get('description', '')} {job.get('company', '')}".lower()
            role_hits = sum(1 for term in role_terms if term in haystack)
            tech_hits = sum(1 for term in tech_terms if term in haystack)
            if role_hits or tech_hits >= 2:
                relevance = "strong"
            elif tech_hits:
                relevance = "possible"
            else:
                relevance = "exploratory" if role_terms or tech_terms else "unscored"
            job["profile_relevance"] = relevance
            annotated.append(job)
        return annotated

    # ----------------------------------------------------------
    # FILTRO EXTRA POR KEYWORDS NEGATIVAS
    # ----------------------------------------------------------

    @staticmethod
    def apply_negative_filter(jobs: List[Dict], experience_level: str = "junior") -> List[Dict]:
        """
        Filtra trabajos usando keywords negativas basadas en el nivel de experiencia del usuario.
        Un Junior no debería ver avisos Senior o Lead. Un Senior no debería ver Pasantías.
        """
        # Keywords negativas base (para todos)
        base_negatives = config.NEGATIVE_KEYWORDS.copy()

        # Keywords negativas dinámicas por nivel
        level_negatives = config.LEVEL_NEGATIVE_KEYWORDS.get(experience_level.lower(), [])
        base_negatives.extend(level_negatives)

        # Deduplicar
        negatives = list(set([n.lower() for n in base_negatives]))

        filtered = []
        level = (experience_level or "").lower()

        for job in jobs:
            title = job.get("title", "")
            text = f"{title} {job.get('description','')} {job.get('company','')} {job.get('location','')}".lower()

            has_negative = False

            # Regla explícita y simple para juniors/sin experiencia:
            # nunca mostrar avisos que mencionen Senior/Sr en el título.
            if level in {"junior", "sin_experiencia"}:
                title_l = title.lower()
                if "senior" in title_l or " sr" in title_l or title_l.startswith("sr "):
                    logger.debug("Filtrado negativo (regla junior): '%s'", title)
                    has_negative = True

            # Si aún no se marcó como negativo, aplicar el filtro general
            if not has_negative:
                for neg in negatives:
                    # Buscamos con bordes de palabra para evitar falsos positivos (ej: "SRE" conteniendo "sr")
                    import re
                    if re.search(r'\b' + re.escape(neg) + r'\b', text):
                        has_negative = True
                        logger.debug("Filtrado negativo: '%s' por keyword '%s'", job.get("title", ""), neg)
                        break

            if not has_negative:
                filtered.append(job)

        return filtered

    # ----------------------------------------------------------
    # FILTRO POR FECHA DE PUBLICACIÓN
    # ----------------------------------------------------------

    @staticmethod
    def apply_date_filter(jobs: List[Dict], max_days: int = 45) -> List[Dict]:
        """
        Elimina trabajos que fueron publicados hace demasiados días.
        Parsea tanto formatos ISO (Remotive/Arbeitnow) como RSS (Google/LinkedIn).
        """
        filtered = []
        now = datetime.datetime.now(datetime.timezone.utc)
        
        for job in jobs:
            date_str = str(job.get("date") or "").strip()
            job_date = JobScraper.parse_job_date(date_str)
            if job_date is None:
                job["date_status"] = "unknown"
                filtered.append(job)
                continue

            job["date_status"] = "published"
            days_old = (now - job_date).days
            if days_old <= max_days:
                filtered.append(job)
            else:
                logger.debug("Filtrado por fecha antigua (%d días): '%s' [%s]", days_old, job.get("title", ""), date_str)
                
        return filtered

    @staticmethod
    def parse_job_date(value: str) -> Optional[datetime.datetime]:
        """Parse common feed/API timestamps to UTC, returning None when uncertain."""
        date_str = str(value or "").strip()
        if not date_str:
            return None
        if date_str.isdigit():
            if len(date_str) < 9:
                return None
            try:
                timestamp = int(date_str)
                if len(date_str) >= 13:
                    timestamp = timestamp / 1000
                return datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
            except (OverflowError, OSError, ValueError):
                return None
        clean_date = date_str.replace("Z", "+00:00")
        try:
            parsed = datetime.datetime.fromisoformat(clean_date)
        except ValueError:
            try:
                parsed = parsedate_to_datetime(date_str)
            except (TypeError, ValueError, OverflowError):
                return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=datetime.timezone.utc)
        return parsed.astimezone(datetime.timezone.utc)

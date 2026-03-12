"""
job_scraper.py - Scrapers para todas las fuentes de empleo

Fuentes implementadas:
  ✅ Remotive API         - API pública gratuita, trabajos remotos IT
  ✅ Arbeitnow API        - API pública gratuita, trabajos remotos/global
  ✅ Jobicy API           - API pública gratuita, trabajos remotos IT
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
import requests
import feedparser
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from typing import List, Dict

import config

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

    # ----------------------------------------------------------
    # BÚSQUEDA PRINCIPAL
    # ----------------------------------------------------------

    def search_all(self, keywords: List[str], location: str = "Buenos Aires", max_age_days: int = 30) -> List[Dict]:
        """
        Busca en todas las fuentes habilitadas para la lista de keywords.
        Retorna una lista de trabajos únicos (deduplicados por URL).
        """
        all_jobs: List[Dict] = []

        # Limitar a 5 keywords por ciclo
        active_keywords = keywords[:5]

        # --- APIs que buscan por query (una request por keyword) ---
        for keyword in active_keywords:
            logger.info("🔍 Buscando: '%s'", keyword)

            if config.SOURCES_ENABLED.get("remotive"):
                self._safe_search("Remotive", self.search_remotive, all_jobs, keyword)
                time.sleep(1)

            if config.SOURCES_ENABLED.get("arbeitnow"):
                self._safe_search("Arbeitnow", self.search_arbeitnow, all_jobs, keyword)
                time.sleep(1)

            if config.SOURCES_ENABLED.get("jobicy"):
                self._safe_search("Jobicy", self.search_jobicy, all_jobs, keyword)
                time.sleep(1)

            if config.SOURCES_ENABLED.get("serpapi_google"):
                self._safe_search("Google Jobs", self.search_google_jobs, all_jobs, keyword, location)
                time.sleep(config.REQUEST_DELAY_SECONDS)

            if config.SOURCES_ENABLED.get("twitter"):
                self._safe_search("Twitter/X", self.search_twitter, all_jobs, keyword)
                time.sleep(config.REQUEST_DELAY_SECONDS)

            # --- Fuentes locales argentinas ---
            if config.SOURCES_ENABLED.get("linkedin_google"):
                self._safe_search("LinkedIn AR", self.search_linkedin_google, all_jobs, keyword, location)
                time.sleep(2)

        # Deduplicar resultados por URL
        seen_urls: set = set()
        unique_jobs: List[Dict] = []
        for job in all_jobs:
            url = job.get("url", "").strip()
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_jobs.append(job)

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
        """Wrapper que ejecuta un scraper con manejo de errores."""
        try:
            jobs = func(*args)
            results.extend(jobs)
            logger.info("  ✅ %s: %d resultado(s)", source_name, len(jobs))
        except Exception as e:
            logger.error("  ❌ %s falló: %s", source_name, e)

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
            logger.error("Jobicy API error: %s", e)
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
    # 7. LINKEDIN JOBS via GOOGLE NEWS RSS — ARGENTINA LOCAL
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
            })

        return jobs

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
        user_loc_lower = user_location.lower()

        # Extraer país y ciudad del usuario
        # "Buenos Aires Argentina" -> ["buenos", "aires", "argentina"]
        user_parts = user_loc_lower.replace(",", " ").split()

        # Palabras de ubicación del usuario para matching
        user_terms = set(user_parts)
        # Agregar variantes comunes si detectamos Argentina o Buenos Aires
        if any(term in ["argentina", "buenos", "aires"] for term in user_terms):
            user_terms.update(config.LOCATION_VARIANTS)

        # Términos que indican "abierto a cualquiera" (se aceptan siempre)
        global_terms = config.GLOBAL_LOCATION_TERMS

        filtered = []
        for job in jobs:
            job_loc = job.get("location", "").lower()

            # Si no tiene ubicación, aceptar (mejor mostrar de más que de menos)
            if not job_loc or job_loc == "n/a":
                filtered.append(job)
                continue

            # Si la ubicación contiene algún término global → aceptar
            if any(g in job_loc for g in global_terms):
                filtered.append(job)
                continue

            # Si la ubicación coincide con algún término del usuario → aceptar
            if any(term in job_loc for term in user_terms):
                filtered.append(job)
                continue

            # Si la ubicación del job es genérica sin país específico → aceptar
            # (ej: solo dice el nombre del puesto, sin ciudad/país)

            # Si llegamos acá, el job tiene una ubicación específica que no coincide → rechazar
            logger.debug("Filtrado por ubicación: '%s' (job: %s)", job_loc, job.get("title", ""))

        return filtered

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
        for job in jobs:
            text = f"{job.get('title','')} {job.get('description','')} {job.get('company','')} {job.get('location','')}".lower()
            
            has_negative = False
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
        import datetime
        from email.utils import parsedate_to_datetime
        
        filtered = []
        now = datetime.datetime.now(datetime.timezone.utc)
        
        for job in jobs:
            date_str = str(job.get("date", "")).strip()
            if not date_str:
                filtered.append(job)
                continue
                
            job_date = None
            
            # Intentar formato ISO
            try:
                if "-" in date_str[:7] and ("T" in date_str or " " in date_str):
                    clean_date = date_str.replace("Z", "+00:00")
                    if clean_date.isdigit():
                        job_date = datetime.datetime.fromtimestamp(int(clean_date), tz=datetime.timezone.utc)
                    else:
                        job_date = datetime.datetime.fromisoformat(clean_date[:25])
            except ValueError:
                pass
                
            # Intentar formato RSS si ISO falló o no aplicaba
            if job_date is None:
                try:
                    if "," in date_str and ":" in date_str:
                        job_date = parsedate_to_datetime(date_str)
                except Exception:
                    pass
                    
            if job_date:
                if job_date.tzinfo is None:
                    job_date = job_date.replace(tzinfo=datetime.timezone.utc)
                
                days_old = (now - job_date).days
                if days_old <= max_days:
                    filtered.append(job)
                else:
                    logger.debug("Filtrado por fecha antigua (%d días): '%s' [%s]", days_old, job.get("title", ""), date_str)
            else:
                # Formato desconocido / error, dejamos pasar
                logger.debug("Error parseando fecha (desconocida): '%s'", date_str)
                filtered.append(job)
                
        return filtered

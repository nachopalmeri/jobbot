"""
config.py - Configuración global del Job Monitor Bot
Carga variables desde el archivo .env automáticamente.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# TELEGRAM
# ============================================================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")

# ============================================================
# APIs OPCIONALES
# ============================================================
# SerpAPI: 100 búsquedas GRATUITAS por mes → https://serpapi.com
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")

# Twitter/X: Requiere plan Basic ($100/mes) para búsqueda.
# El plan free solo permite postear, NO buscar.
# Obtenelo en https://developer.twitter.com
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")

# ============================================================
# BASE DE DATOS Y ARCHIVOS
# ============================================================
DATABASE_TYPE = os.getenv("DATABASE_TYPE", "sqlite").lower()
DATABASE_PATH = os.getenv("DATABASE_PATH", "job_bot.db")
CV_STORAGE_PATH = os.getenv("CV_STORAGE_PATH", "cvs/")

# Supabase (Postgres)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")  # URL de conexión directa a PG

# ============================================================
# SCHEDULER (per-user — valores almacenados en DB por usuario)
# ============================================================
# El intervalo real es por usuario (3-24h), estos son los límites
MIN_CHECK_INTERVAL_HOURS = 3
MAX_CHECK_INTERVAL_HOURS = 24
DEFAULT_CHECK_INTERVAL_HOURS = 6
# Cada cuántos minutos el scheduler revisa si hay usuarios pendientes
SCHEDULER_POLL_MINUTES = int(os.getenv("SCHEDULER_POLL_MINUTES", "10"))

# ============================================================
# GROQ API (para CV Analyzer — Llama 3.3 70B)
# ============================================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# ============================================================
# BÚSQUEDA - Defaults para Buenos Aires
# ============================================================
DEFAULT_LOCATION = "Buenos Aires Argentina"

# Keywords por defecto (se usan si el usuario no configura las suyas)
DEFAULT_KEYWORDS = [
    "Python junior",
    "backend trainee",
    "desarrollador junior",
    "pasantía IT",
    "pasantia programacion",
    "SQL developer junior",
    "fullstack junior",
    "web developer junior",
]

# Palabras que EXCLUYEN un resultado (para no mostrar roles senior)
NEGATIVE_KEYWORDS = [
    "senior", "10 años de experiencia", "8 años", "7 años",
    "lead developer", "tech lead", "arquitecto", "5+ años",
]

# Keywords negativas específicas por nivel de experiencia
LEVEL_NEGATIVE_KEYWORDS = {
    "sin_experiencia": [
        "senior", "sr", "lead", "manager", "staff", "principal", "director",
        "head", "arquitecto", "architect", "expert", "experto",
        "3 años", "4 años", "5 años", "3 years", "4 years", "5 years",
        "ssr", "semi senior", "semi-senior"
    ],
    "junior": [
        "senior", "sr", "lead", "manager", "staff", "principal", "director",
        "head", "arquitecto", "architect", "expert", "experto",
        "3 años", "4 años", "5 años", "3 years", "4 years", "5 years",
        "ssr", "semi senior", "semi-senior"
    ],
    "semi_senior": [
        "lead", "manager", "staff", "principal", "director", "head",
        "trainee", "pasantía", "pasantia", "intern", "internship"
    ],
    "senior": [
        "trainee", "pasantía", "pasantia", "intern", "internship",
        "junior", "jr", "entry level"
    ]
}

# ============================================================
# FILTROS DE UBICACIÓN
# ============================================================
# Variantes para detectar Argentina/LATAM (usado para emparejar ubicación del usuario)
LOCATION_VARIANTS = [
    "argentina", "ar", "buenos aires", "latam",
    "latin america", "south america", "sudamérica",
    "sudamerica", "latinoamérica", "latinoamerica",
    "americas", "america"
]

# Términos que indican que un trabajo es global/remoto y aceptable siempre
GLOBAL_LOCATION_TERMS = {
    "anywhere", "worldwide", "global", "globally", "remote",
    "🌐", "remoto", "international", "all countries",
    "any location", "no restriction", "earth",
    "americas", "america", "latam", "latin america",
    "south america"
}

# ============================================================
# FUENTES - Activar/desactivar scrapers
# ============================================================
# APIs gratuitas que funcionan sin key:
SOURCES_ENABLED = {
    "linkedin_google": True,            # LinkedIn AR via Google News RSS (local!) ✅
    "remotive":        True,            # API pública gratuita (trabajos remotos IT) ✅
    "arbeitnow":       True,            # API pública gratuita (trabajos remotos/global) ✅
    "jobicy":          True,            # API pública gratuita (trabajos remotos IT) ✅
    "himalayas":       True,            # API pública gratuita (remotos/tech) ✅
    "custom_rss":      True,            # Feeds personalizados del usuario ✅
    "serpapi_google":  bool(SERPAPI_KEY),       # Requiere API key de SerpAPI
    "twitter":         bool(TWITTER_BEARER_TOKEN),  # Requiere plan Basic de Twitter
}

# ============================================================
# RATE LIMITING - Para no quemar los servidores ni ser baneado
# ============================================================
REQUEST_DELAY_SECONDS = 3      # Pausa entre requests a sitios externos
MAX_RESULTS_PER_SOURCE = 10    # Máximo de resultados por fuente por keyword
MAX_JOBS_PER_NOTIFICATION = 15 # Máximo de ofertas enviadas en un ciclo
REQUEST_TIMEOUT = 12           # Timeout en segundos para cada request HTTP

# ============================================================
# STATS API - Endpoint público para la landing page
# ============================================================
STATS_API_PORT = int(os.getenv("STATS_API_PORT", "8080"))
STATS_API_ENABLED = os.getenv("STATS_API_ENABLED", "true").lower() == "true"

# ============================================================
# LANDING PAGE - URL para el comando /web
# ============================================================
LANDING_URL = os.getenv("LANDING_URL", "https://jobbot-landing.vercel.app")

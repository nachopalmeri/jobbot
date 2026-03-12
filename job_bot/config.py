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
DATABASE_PATH = os.getenv("DATABASE_PATH", "job_bot.db")
CV_STORAGE_PATH = os.getenv("CV_STORAGE_PATH", "cvs/")

# ============================================================
# SCHEDULER
# ============================================================
# Intervalo entre chequeos automáticos (en horas)
# 2 horas = buen balance entre frescura y no sobrecargar las fuentes
CHECK_INTERVAL_HOURS = int(os.getenv("CHECK_INTERVAL_HOURS", "2"))

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
    "linkedin_google":  True,            # LinkedIn AR via Google News RSS (local!) ✅
    "remotive":        True,            # API pública gratuita (trabajos remotos IT) ✅
    "arbeitnow":       True,            # API pública gratuita (trabajos remotos/global) ✅
    "jobicy":          True,            # API pública gratuita (trabajos remotos IT) ✅
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

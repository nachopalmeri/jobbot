"""
company_service.py - Servicio de datos de empresas usando LinkedIn Data API

Cachea información de empresas para evitar llamadas repetidas a la API.
TTL de caché: 7 días por defecto.
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Optional

import requests

try:
    import config
except ImportError:
    from job_bot import config

try:
    from database import Database
except ImportError:
    from job_bot.database import Database

logger = logging.getLogger(__name__)

# TTL de caché en segundos (7 días)
CACHE_TTL_SECONDS = 7 * 24 * 60 * 60


def get_company_by_domain(domain: str, db: Optional[Database] = None) -> Optional[Dict]:
    """
    Obtiene información de una empresa por su dominio.
    
    1. Primero busca en caché local (SQLite)
    2. Si no existe o está expirada, consulta LinkedIn Data API
    3. Guarda en caché y retorna
    
    Args:
        domain: Dominio de la empresa (ej: "google.com")
        db: Instancia de Database (opcional, se crea si no se pasa)
    
    Returns:
        Dict con datos de la empresa o None si no se encuentra
    """
    if not domain or '.' not in domain:
        return None
    
    domain = domain.strip().lower()
    
    # Normalizar dominio (quitar www., etc.)
    domain = _normalize_domain(domain)
    
    # Usar DB proporcionada o crear nueva
    if db is None:
        db = Database()
    
    # 1. Buscar en caché
    cached = db.get_company_data(domain)
    if cached:
        # Verificar si no está expirada
        cached_at = cached.get('cached_at', 0)
        if time.time() - cached_at < CACHE_TTL_SECONDS:
            logger.info(f"[CACHE HIT] Empresa {domain}")
            return cached['data']
        logger.info(f"[CACHE EXPIRED] Empresa {domain}")
    
    # 2. Consultar API
    company_data = _fetch_from_api(domain)
    
    if company_data:
        # 3. Guardar en caché
        db.set_company_data(domain, company_data)
        logger.info(f"[API FETCH] Empresa {domain} guardada en caché")
    
    return company_data


def _normalize_domain(domain: str) -> str:
    """Normaliza el dominio quitando www., paths, etc."""
    domain = domain.strip().lower()
    
    # Quitar protocolo
    if '://' in domain:
        domain = domain.split('://')[1]
    
    # Quitar www.
    if domain.startswith('www.'):
        domain = domain[4:]
    
    # Quitar paths, query params, etc.
    domain = domain.split('/')[0].split('?')[0].split('#')[0]
    
    return domain


def _fetch_from_api(domain: str) -> Optional[Dict]:
    """
    Consulta LinkedIn Data API para obtener datos de la empresa.
    """
    if not config.RAPIDAPI_KEY:
        logger.warning("RAPIDAPI_KEY no configurada, no se puede consultar datos de empresa")
        return None
    
    url = f"https://{config.RAPIDAPI_LINKEDIN_DATA_HOST}/get-company-by-domain"
    
    querystring = {"domain": domain}
    
    headers = {
        "X-RapidAPI-Key": config.RAPIDAPI_KEY,
        "X-RapidAPI-Host": config.RAPIDAPI_LINKEDIN_DATA_HOST
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Normalizar y estructurar la respuesta
            return _normalize_api_response(data, domain)
        
        elif response.status_code == 429:
            logger.warning(f"[RATE LIMIT] LinkedIn Data API para {domain}")
            return None
        
        else:
            logger.warning(f"[API ERROR] {response.status_code} para {domain}: {response.text[:200]}")
            return None
            
    except requests.exceptions.Timeout:
        logger.warning(f"[TIMEOUT] Consultando empresa {domain}")
        return None
    except Exception as e:
        logger.error(f"[ERROR] Consultando empresa {domain}: {e}")
        return None


def _normalize_api_response(data: Dict, domain: str) -> Dict:
    """
    Normaliza la respuesta de la API a un formato consistente.
    """
    # La API puede devolver data directamente o envuelta
    if isinstance(data, list) and len(data) > 0:
        company = data[0]
    elif isinstance(data, dict):
        company = data
    else:
        return {
            "domain": domain,
            "name": domain.split('.')[0].capitalize(),
            "description": "Información no disponible",
            "industry": "N/A",
            "company_size": "N/A",
            "location": "N/A",
            "website": f"https://{domain}",
            "linkedin_url": None,
            "logo": None,
            "specialities": [],
            "founded": None,
            "type": "N/A"
        }
    
    return {
        "domain": domain,
        "name": _safe_get(company, "name", domain.split('.')[0].capitalize()),
        "description": _safe_get(company, "description", "Sin descripción disponible"),
        "industry": _safe_get(company, "industry", "N/A"),
        "company_size": _safe_get(company, "company_size", "N/A"),
        "employee_count": _safe_get(company, "employee_count", None),
        "location": _safe_get(company, "hq", _safe_get(company, "location", "N/A")),
        "website": _safe_get(company, "website", f"https://{domain}"),
        "linkedin_url": _safe_get(company, "linkedin_url", None),
        "logo": _safe_get(company, "logo", None),
        "specialities": _safe_get_list(company, "specialities", []),
        "founded": _safe_get(company, "founded", None),
        "type": _safe_get(company, "type", "N/A"),
        "funding_total": _safe_get(company, "funding_total", None)
    }


def _safe_get(data: Dict, key: str, default=None):
    """Obtiene un valor de forma segura."""
    value = data.get(key)
    if value is None or value == "":
        return default
    return value


def _safe_get_list(data: Dict, key: str, default=None):
    """Obtiene una lista de forma segura."""
    value = data.get(key)
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [value]
    return default or []


def format_company_info(company_data: Dict) -> str:
    """
    Formatea los datos de la empresa para mostrar en Telegram.
    """
    if not company_data:
        return "❌ No se encontró información de la empresa."
    
    name = company_data.get('name', 'N/A')
    domain = company_data.get('domain', 'N/A')
    description = company_data.get('description', 'Sin descripción')
    industry = company_data.get('industry', 'N/A')
    size = company_data.get('company_size', company_data.get('employee_count', 'N/A'))
    location = company_data.get('location', 'N/A')
    website = company_data.get('website', f'https://{domain}')
    linkedin = company_data.get('linkedin_url', '')
    specialities = company_data.get('specialities', [])
    founded = company_data.get('founded', '')
    
    lines = [
        f"🏢 <b>{name}</b>",
        f"🌐 {domain}",
        ""
    ]
    
    if description and description != "Sin descripción disponible":
        # Truncar descripción larga
        desc = description[:200] + "..." if len(description) > 200 else description
        lines.append(f"📝 {desc}")
        lines.append("")
    
    if industry and industry != "N/A":
        lines.append(f"💼 Industria: {industry}")
    
    if size and size != "N/A":
        lines.append(f"👥 Tamaño: {size}")
    
    if location and location != "N/A":
        lines.append(f"📍 Ubicación: {location}")
    
    if founded:
        lines.append(f"📅 Fundada: {founded}")
    
    if specialities and len(specialities) > 0:
        specs = ", ".join(specialities[:5])  # Max 5 especialidades
        lines.append(f"✨ Especialidades: {specs}")
    
    lines.append("")
    lines.append(f"🔗 <a href='{website}'>Sitio web</a>")
    
    if linkedin:
        lines.append(f"💼 <a href='{linkedin}'>LinkedIn</a>")
    
    return "\n".join(lines)

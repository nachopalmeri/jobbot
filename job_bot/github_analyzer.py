"""
github_analyzer.py - Analizador de perfiles de GitHub con IA
Extrae repositorios, lenguajes y descripciones para match laboral.
"""

import httpx
import logging
import asyncio
from typing import List, Dict, Optional

try:
    import config
except ImportError:
    from job_bot import config

logger = logging.getLogger(__name__)

async def fetch_github_repos(username: str) -> List[Dict]:
    """Obtiene la lista de repositorios públicos de un usuario de GitHub."""
    if not username:
        return []
    
    # Limpiar el username si es una URL completa
    username = username.split("/")[-1]
    
    url = f"https://api.github.com/users/{username}/repos?sort=updated&per_page=15"
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            if response.status_code == 200:
                repos = response.json()
                return [
                    {
                        "name": r.get("name"),
                        "description": r.get("description"),
                        "language": r.get("language"),
                        "stars": r.get("stargazers_count"),
                        "url": r.get("html_url")
                    }
                    for r in repos if not r.get("fork")
                ]
            else:
                logger.error(f"Error GitHub API: {response.status_code}")
                return []
    except Exception as e:
        logger.error(f"Error fetching GitHub repos: {e}")
        return []

def format_github_summary(repos: List[Dict]) -> str:
    """Crea un resumen de texto de los repositorios para la IA."""
    if not repos:
        return "No se encontraron repositorios públicos."
    
    summary = "Proyectos destacados en GitHub:\n"
    for r in repos[:10]:
        desc = r['description'] if r['description'] else "Sin descripción"
        summary += f"- {r['name']} ({r['language']}): {desc} | ⭐ {r['stars']}\n"
    return summary

async def analyze_github_match(repos: List[Dict], job_description: str) -> str:
    """Usa Groq para analizar si el portfolio de GitHub encaja con la oferta."""
    from cv_analyzer import analyze_with_groq # Import dinámico para evitar circulares
    
    github_text = format_github_summary(repos)
    
    prompt = f"""
    Eres un Technical Recruiter experto. Analiza el siguiente portfolio de GitHub y compáralo con la descripción del puesto.
    
    PORTFOLIO GITHUB:
    {github_text}
    
    DESCRIPCIÓN DEL PUESTO:
    {job_description}
    
    TAREA:
    1. Identifica los 2 proyectos que más valor aportan para este puesto específico.
    2. Da una breve explicación de por qué esos proyectos son relevantes.
    3. Sugiere una "frase de oro" para que el candidato use en su postulación mencionando su GitHub.
    4. Da un 'Match Score' del 1 al 10 basado SOLO en el código/proyectos vistos.
    
    Responde en español, de forma profesional y motivadora.
    """
    
    return await analyze_with_groq(prompt)

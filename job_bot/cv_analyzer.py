"""
cv_analyzer.py — Análisis de CV vs Ofertas de Trabajo

Funcionalidades:
  ✅ Parseo de CV (PDF y TXT)
  ✅ Extracción de keywords del CV
  ✅ Comparación CV vs oferta → score + sugerencias
  ✅ Tips accionables vía Gemini API (si hay key configurada)
"""

import logging
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from collections import Counter

try:
    import config
except ImportError:
    from job_bot import config

logger = logging.getLogger(__name__)

# ============================================================
# KEYWORDS TÉCNICAS COMUNES (para matching rápido sin LLM)
# ============================================================
TECH_KEYWORDS = {
    # Lenguajes
    "python", "javascript", "typescript", "java", "c#", "c++", "go", "golang",
    "ruby", "php", "swift", "kotlin", "rust", "scala", "r", "matlab",
    # Frameworks
    "react", "angular", "vue", "vuejs", "nextjs", "next.js", "django", "flask",
    "fastapi", "express", "nestjs", "spring", "rails", "laravel", ".net",
    "svelte", "nuxt", "remix",
    # Bases de datos
    "sql", "mysql", "postgresql", "postgres", "mongodb", "redis", "sqlite",
    "dynamodb", "cassandra", "elasticsearch", "supabase", "firebase",
    # Cloud & DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "k8s", "terraform",
    "jenkins", "github actions", "ci/cd", "linux", "nginx", "apache",
    # Data
    "pandas", "numpy", "tensorflow", "pytorch", "scikit-learn", "spark",
    "airflow", "dbt", "tableau", "power bi", "etl",
    # Otros
    "git", "rest", "graphql", "api", "microservices", "agile", "scrum",
    "jira", "figma", "html", "css", "sass", "tailwind", "bootstrap",
    "node", "nodejs", "node.js", "npm", "yarn",
}

# Keywords de experiencia/soft skills
SOFT_KEYWORDS = {
    "liderazgo", "leadership", "comunicación", "teamwork", "trabajo en equipo",
    "problem solving", "resolución de problemas", "gestión de proyectos",
    "project management", "metodologías ágiles", "agile", "scrum",
    "mentoring", "coaching", "negociación", "presentaciones",
}


# ============================================================
# PARSEO DE CV
# ============================================================

def parse_cv(cv_path: str) -> Optional[str]:
    """
    Extrae texto de un CV (PDF o TXT).
    Retorna el texto limpio o None si falla.
    """
    path = Path(cv_path)
    if not path.exists():
        logger.error("CV no encontrado: %s", cv_path)
        return None

    try:
        if path.suffix.lower() == ".pdf":
            return _parse_pdf(path)
        elif path.suffix.lower() == ".txt":
            return path.read_text(encoding="utf-8", errors="ignore")
        else:
            logger.warning("Formato de CV no soportado: %s", path.suffix)
            return None
    except Exception as e:
        logger.error("Error parseando CV %s: %s", cv_path, e)
        return None


def _parse_pdf(path: Path) -> Optional[str]:
    """Extrae texto de un PDF usando pdfplumber."""
    try:
        import pdfplumber
    except ImportError:
        logger.error("pdfplumber no instalado. Ejecutá: pip install pdfplumber")
        return None

    text_parts = []
    try:
        with pdfplumber.open(str(path)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
    except Exception as e:
        logger.error("Error leyendo PDF: %s", e)
        return None

    return "\n".join(text_parts) if text_parts else None


# ============================================================
# EXTRACCIÓN DE KEYWORDS
# ============================================================

def extract_keywords(text: str) -> Dict[str, List[str]]:
    """
    Extrae keywords técnicas y soft skills de un texto.
    Retorna un dict con 'tech' y 'soft' como listas.
    """
    if not text:
        return {"tech": [], "soft": []}

    text_lower = text.lower()
    # Normalizar separadores comunes
    text_normalized = re.sub(r'[/|,;•·\-]', ' ', text_lower)
    words = set(text_normalized.split())

    found_tech = []
    for kw in TECH_KEYWORDS:
        # Para keywords de múltiples palabras (e.g. "github actions")
        if " " in kw:
            if kw in text_lower:
                found_tech.append(kw)
        elif kw in words:
            found_tech.append(kw)

    found_soft = []
    for kw in SOFT_KEYWORDS:
        if " " in kw:
            if kw in text_lower:
                found_soft.append(kw)
        elif kw in words:
            found_soft.append(kw)

    return {
        "tech": sorted(set(found_tech)),
        "soft": sorted(set(found_soft)),
    }


# ============================================================
# COMPARACIÓN CV vs OFERTA
# ============================================================

def compare_cv_with_offer(cv_text: str, offer_text: str) -> Dict:
    """
    Compara keywords del CV con keywords de la oferta.
    Retorna un dict con:
      - matching: keywords que aparecen en ambos
      - missing: keywords de la oferta que NO aparecen en el CV
      - score: porcentaje de match (0-100)
      - suggestions: lista de sugerencias accionables
    """
    cv_kws = extract_keywords(cv_text)
    offer_kws = extract_keywords(offer_text)

    # Combinar tech + soft para comparación
    cv_all = set(cv_kws["tech"] + cv_kws["soft"])
    offer_all = set(offer_kws["tech"] + offer_kws["soft"])

    matching = cv_all & offer_all
    missing = offer_all - cv_all
    extra = cv_all - offer_all  # Lo que tiene el CV pero no pide la oferta

    # Score basado en cuántas keywords de la oferta cubrimos
    if len(offer_all) == 0:
        score = 50  # No podemos calcular, asumimos neutral
    else:
        score = int((len(matching) / len(offer_all)) * 100)

    # Generar sugerencias
    suggestions = _generate_suggestions(matching, missing, score)

    return {
        "matching": sorted(matching),
        "missing": sorted(missing),
        "extra": sorted(extra),
        "score": min(score, 100),
        "cv_keywords": cv_kws,
        "offer_keywords": offer_kws,
        "suggestions": suggestions,
    }


def _generate_suggestions(matching: set, missing: set, score: int) -> List[str]:
    """Genera sugerencias accionables basadas en la comparación."""
    suggestions = []

    if missing:
        top_missing = list(missing)[:5]
        suggestions.append(
            f"📝 Agregá estas keywords a tu CV: {', '.join(top_missing)}"
        )

    if score >= 80:
        suggestions.append("🎯 ¡Excelente match! Tu CV ya cubre la mayoría de requisitos.")
    elif score >= 60:
        suggestions.append("🟡 Buen match. Ajustá tu CV mencionando las keywords faltantes.")
    elif score >= 40:
        suggestions.append("🟠 Match parcial. Considerá resaltar tu experiencia con las tecnologías pedidas.")
    else:
        suggestions.append("🔴 Match bajo. Esta oferta pide habilidades que no aparecen en tu CV.")

    if missing:
        suggestions.append(
            "💡 Tip: No solo agregues las palabras — describí proyectos donde las usaste."
        )

    return suggestions


# ============================================================
# FORMATO PARA TELEGRAM
# ============================================================

def format_cv_analysis(analysis: Dict) -> str:
    """Formatea el análisis para enviar por Telegram (HTML)."""
    score = analysis["score"]
    matching = analysis["matching"]
    missing = analysis["missing"]
    suggestions = analysis["suggestions"]

    # Score emoji
    if score >= 80:
        score_emoji = "🟢"
    elif score >= 60:
        score_emoji = "🟡"
    elif score >= 40:
        score_emoji = "🟠"
    else:
        score_emoji = "🔴"

    lines = [
        f"📊 <b>Análisis CV vs Oferta</b>",
        f"━━━━━━━━━━━━━━━━━━━━━━━",
        f"{score_emoji} Match: <b>{score}%</b>",
        "",
    ]

    if matching:
        lines.append(f"✅ <b>Keywords que coinciden ({len(matching)}):</b>")
        lines.append(f"  {', '.join(matching)}")
        lines.append("")

    if missing:
        lines.append(f"❌ <b>Te faltan ({len(missing)}):</b>")
        lines.append(f"  {', '.join(missing)}")
        lines.append("")

    if suggestions:
        lines.append("<b>💡 Sugerencias:</b>")
        for s in suggestions:
            lines.append(f"  {s}")

    return "\n".join(lines)


def format_job_with_score(job: Dict, cv_text: str) -> Tuple[Dict, int]:
    """
    Analiza un job contra el CV y retorna (job_enriquecido, score).
    Agrega campos 'match_score' y 'match_info' al job.
    """
    offer_text = f"{job.get('title', '')} {job.get('description', '')} {job.get('company', '')}"
    analysis = compare_cv_with_offer(cv_text, offer_text)

    job_enriched = job.copy()
    job_enriched["match_score"] = analysis["score"]

    missing_top = analysis["missing"][:3]
    if missing_top:
        job_enriched["match_info"] = f"Te faltan: {', '.join(missing_top)}"
    else:
        job_enriched["match_info"] = "¡Tu CV cubre los requisitos!"

    return job_enriched, analysis["score"]


# ============================================================
# GROQ API — ANÁLISIS AVANZADO (opcional)
# ============================================================

async def analyze_with_gemini(cv_text: str, offer_text: str = "") -> Optional[str]:
    """
    Usa la API de Groq (Llama 3.3 70B) para generar sugerencias avanzadas de CV.
    Retorna el texto de la sugerencia o None si no hay key/error.
    Mantiene el nombre de la función `analyze_with_gemini` por retrocompatibilidad.
    """
    if not config.GROQ_API_KEY:
        logger.info("Groq API key no configurada, usando análisis local.")
        return None

    try:
        from groq import AsyncGroq
    except ImportError:
        logger.warning("Librería groq no instalada. Usando análisis local.")
        return None

    try:
        # Groq client uses GROQ_API_KEY env var automatically if passed,
        # but we explicitly pass the loaded config value to be safe.
        client = AsyncGroq(api_key=config.GROQ_API_KEY)
        model_name = config.GROQ_MODEL

        if offer_text:
            system_prompt = "Sos un experto en recursos humanos y búsqueda laboral en Argentina/LatAm. Format: bullets cortos, en español, sin burocracia."
            prompt = f"""Analizá este CV y esta oferta de trabajo. Dá exactamente 3-5 sugerencias CONCRETAS y ACCIONABLES para mejorar el CV para esta oferta específica.

CV del candidato:
{cv_text[:3000]}

Oferta de trabajo:
{offer_text[:2000]}

Sugerencias (máximo 5 bullets):"""
        else:
            system_prompt = "Sos un experto en recursos humanos y búsqueda laboral en Argentina/LatAm. Format: bullets cortos, en español, sin burocracia."
            prompt = f"""Analizá este CV y dá exactamente 3-5 sugerencias CONCRETAS y ACCIONABLES para mejorarlo.
Enfocate en: keywords técnicas que faltan, estructura, y cómo destacar contra otros candidatos.

CV del candidato:
{cv_text[:3000]}

Sugerencias (máximo 5 bullets):"""

        chat_completion = await client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=model_name,
            temperature=0.3,
            max_tokens=500,
        )
        return chat_completion.choices[0].message.content

    except Exception as e:
        logger.error("Error con Groq API: %s", e)
        return None


async def generate_interview_questions(cv_text: str, role_type: str = "") -> Optional[str]:
    """
    Genera 5 preguntas de entrevista para el candidato basadas en su CV y el rol que busca.
    """
    if not config.GROQ_API_KEY:
        return None

    try:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=config.GROQ_API_KEY)
        
        prompt = f"""Sos un reclutador técnico (IT Recruiter) en Argentina. 
        Basado en el CV del candidato y el rol que busca ({role_type}), generá exactamente 5 preguntas de entrevista.
        
        Dinámica:
        1. Deben ser 3 técnicas y 2 de soft skills/comportamiento.
        2. Deben ser desafiantes pero acordes a su nivel declarado.
        3. Formato: Solo las preguntas, numeradas del 1 al 5.
        
        CV del candidato:
        {cv_text[:3000]}
        
        Preguntas:"""

        chat_completion = await client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=config.GROQ_MODEL,
            temperature=0.7,
            max_tokens=600,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error("Error generando preguntas: %s", e)
        return None


async def evaluate_interview_answer(question: str, answer: str, cv_text: str) -> Optional[str]:
    """
    Evalúa la respuesta de un usuario a una pregunta de entrevista.
    """
    if not config.GROQ_API_KEY:
        return None

    try:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=config.GROQ_API_KEY)
        
        prompt = f"""Sos un reclutador técnico evaluando las respuestas de un candidato.
        
        Pregunta realizada: {question}
        Respuesta del candidato: {answer}
        CV del candidato para contexto: {cv_text[:1500]}
        
        Tu evaluación debe:
        1. Dar una calificación del 1 al 10 (ej: 🟢 8/10).
        2. Explicar brevemente qué estuvo bien y qué faltó.
        3. Dar el "Tip de Oro": qué debería decir para que el reclutador lo ame.
        
        Formato: Corto, directo, en español de Argentina (tuteo), sin introducciones largas.
        """

        chat_completion = await client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=config.GROQ_MODEL,
            temperature=0.4,
            max_tokens=500,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error("Error evaluando respuesta: %s", e)
        return None


async def generate_cover_letter(cv_text: str, role_info: str) -> Optional[str]:
    """
    Genera una carta de presentación (Cover Letter) basada en el CV y la descripción del puesto.
    """
    if not config.GROQ_API_KEY:
        return None

    try:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=config.GROQ_API_KEY)
        
        prompt = f"""Sos un redactor experto en talento.
        Basado en el CV del candidato y la descripción del puesto/role ({role_info}), escribí una CARTA DE PRESENTACIÓN (Cover Letter) atractiva.
        
        Requisitos:
        1. Estilo: Profesional pero con personalidad, tono cercano (tuteo), español de Argentina.
        2. Formato: Máximo 3 párrafos cortos.
        3. Foco: Destacar cómo los skills del candidato resuelven los problemas del puesto.
        
        CV del candidato:
        {cv_text[:3000]}
        
        Info del puesto:
        {role_info[:2000]}
        
        Carta de presentación:"""

        chat_completion = await client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=config.GROQ_MODEL,
            temperature=0.6,
            max_tokens=800,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error("Error generando cover letter: %s", e)
        return None

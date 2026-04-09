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

ROLE_KEYWORDS = {
    "backend": {
        "backend", "back-end", "api", "apis", "microservices", "fastapi",
        "django", "flask", "spring", "java", "python", "node", "golang",
    },
    "frontend": {
        "frontend", "front-end", "react", "nextjs", "next.js", "vue",
        "angular", "typescript", "javascript", "html", "css", "tailwind",
    },
    "fullstack": {
        "fullstack", "full-stack", "full stack", "frontend", "backend",
        "react", "node", "typescript", "javascript", "python",
    },
    "data": {
        "data", "analytics", "analyst", "bi", "etl", "pandas", "numpy",
        "spark", "airflow", "dbt", "tableau", "power bi", "machine learning",
    },
    "devops": {
        "devops", "platform", "sre", "aws", "azure", "gcp", "docker",
        "kubernetes", "terraform", "ci/cd", "jenkins",
    },
    "mobile": {
        "mobile", "android", "ios", "swift", "kotlin", "flutter",
        "react native",
    },
    "qa": {
        "qa", "quality assurance", "testing", "test automation",
        "selenium", "cypress", "pytest",
    },
}

SENIORITY_PATTERNS = {
    "entry": [
        r"\btrainee\b", r"\bintern(ship)?\b", r"\bentry level\b",
        r"\bsin experiencia\b", r"\bpasant[ií]a\b",
    ],
    "junior": [r"\bjunior\b", r"\bjr\b"],
    "semi_senior": [r"\bsemi[ -]?senior\b", r"\bssr\b", r"\bmid(?:dle)?\b"],
    "senior": [r"\bsenior\b", r"\bsr\b", r"\bexpert\b"],
    "lead": [r"\blead\b", r"\bstaff\b", r"\bprincipal\b", r"\bhead\b", r"\bmanager\b"],
}

SENIORITY_ORDER = {
    "entry": 0,
    "junior": 1,
    "semi_senior": 2,
    "senior": 3,
    "lead": 4,
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


def build_profile_context(profile: Dict) -> str:
    """Construye un texto mínimo del perfil para reutilizar el mismo motor de matching."""
    if not profile:
        return ""

    fragments: List[str] = []
    experience_level = (profile.get("experience_level") or "").strip()
    role_type = (profile.get("role_type") or "").strip()
    technologies = (profile.get("technologies") or "").strip()
    modality = (profile.get("job_modality") or "").strip()
    schedule = (profile.get("job_schedule") or "").strip()

    if experience_level:
        fragments.append(f"Nivel: {experience_level}")
    if role_type:
        fragments.append(f"Rol objetivo: {role_type}")
    if technologies:
        fragments.append(f"Tecnologías: {technologies}")
    if modality and modality != "cualquiera":
        fragments.append(f"Modalidad preferida: {modality}")
    if schedule and schedule != "cualquiera":
        fragments.append(f"Jornada preferida: {schedule}")

    return "\n".join(fragments)


def _extract_role_focus(text: str) -> List[str]:
    text_lower = (text or "").lower()
    found = []
    for role, tokens in ROLE_KEYWORDS.items():
        if any(token in text_lower for token in tokens):
            found.append(role)
    return found


def _extract_seniority_signal(text: str) -> Optional[str]:
    text_lower = (text or "").lower()
    for seniority, patterns in reversed(list(SENIORITY_PATTERNS.items())):
        if any(re.search(pattern, text_lower) for pattern in patterns):
            return seniority
    return None


def _seniority_alignment(cv_level: Optional[str], offer_level: Optional[str]) -> tuple[int, Optional[str]]:
    if not offer_level:
        return 10, None
    if not cv_level:
        return 4, "La oferta marca seniority y tu CV no da señales claras de ese nivel."

    cv_rank = SENIORITY_ORDER.get(cv_level, 1)
    offer_rank = SENIORITY_ORDER.get(offer_level, 1)
    if cv_rank == offer_rank:
        return 10, None
    if cv_rank > offer_rank:
        return 8, None
    if offer_rank - cv_rank == 1:
        return 4, "La oferta parece pedir un seniority un poco más alto que el que muestra tu CV."
    return 0, "La oferta pide un seniority bastante más alto que el que muestra tu CV."


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

    cv_tech = set(cv_kws["tech"])
    offer_tech = set(offer_kws["tech"])
    cv_soft = set(cv_kws["soft"])
    offer_soft = set(offer_kws["soft"])

    cv_all = cv_tech | cv_soft
    offer_all = offer_tech | offer_soft

    matching = cv_all & offer_all
    missing = offer_all - cv_all
    extra = cv_all - offer_all

    cv_roles = set(_extract_role_focus(cv_text))
    offer_roles = set(_extract_role_focus(offer_text))
    role_overlap = cv_roles & offer_roles

    cv_seniority = _extract_seniority_signal(cv_text)
    offer_seniority = _extract_seniority_signal(offer_text)

    score = 15

    if offer_tech:
        score += round((len(cv_tech & offer_tech) / len(offer_tech)) * 55)
    elif cv_tech:
        score += 10

    if offer_soft:
        score += round((len(cv_soft & offer_soft) / len(offer_soft)) * 10)

    if offer_roles:
        score += 15 if role_overlap else 0
    else:
        score += 8 if cv_roles else 0

    seniority_points, seniority_warning = _seniority_alignment(cv_seniority, offer_seniority)
    score += seniority_points

    penalties = []
    if offer_roles and cv_roles and not role_overlap:
        score -= 20
        penalties.append("El rol de la oferta no coincide con el foco principal que muestra tu CV.")
    if offer_tech and not (cv_tech & offer_tech):
        score -= 15
        penalties.append("Tu CV no cubre ninguna de las tecnologías principales que aparecen en la oferta.")
    if seniority_warning:
        penalties.append(seniority_warning)

    score = max(0, min(score, 100))

    suggestions = _generate_suggestions(
        matching=matching,
        missing=missing,
        score=score,
        penalties=penalties,
        role_overlap=sorted(role_overlap),
        offer_roles=sorted(offer_roles),
    )

    return {
        "matching": sorted(matching),
        "missing": sorted(missing),
        "extra": sorted(extra),
        "score": score,
        "cv_keywords": cv_kws,
        "offer_keywords": offer_kws,
        "suggestions": suggestions,
        "role_alignment": sorted(role_overlap),
        "offer_roles": sorted(offer_roles),
        "cv_roles": sorted(cv_roles),
        "cv_seniority": cv_seniority,
        "offer_seniority": offer_seniority,
        "penalties": penalties,
    }


def _generate_suggestions(
    matching: set,
    missing: set,
    score: int,
    penalties: List[str],
    role_overlap: List[str],
    offer_roles: List[str],
) -> List[str]:
    """Genera sugerencias accionables basadas en la comparación."""
    suggestions = []

    if penalties:
        suggestions.extend(penalties[:2])

    if missing:
        top_missing = sorted(missing)[:5]
        suggestions.append(
            f"📝 Agregá estas keywords a tu CV: {', '.join(top_missing)}"
        )

    if offer_roles and not role_overlap:
        suggestions.append(
            f"El puesto apunta más a {', '.join(offer_roles)} que a lo que hoy transmite tu CV."
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

    if analysis["penalties"]:
        job_enriched["match_info"] = analysis["penalties"][0]
    elif analysis["missing"]:
        missing_top = analysis["missing"][:3]
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


# ============================================================
# ENTREVISTAS RRHH - Nuevas funciones para método STAR
# ============================================================

async def generate_rrhh_interview_questions(
    cv_text: str, 
    role_type: str = "", 
    company_name: str = None,
    company_data: Dict = None,
    question_count: int = 5
) -> Optional[List[Dict]]:
    """
    Genera preguntas de entrevista RRHH usando el pool de interview_data.py.
    
    Args:
        cv_text: Texto del CV del candidato
        role_type: Rol que busca (ej: "backend", "frontend")
        company_name: Nombre de la empresa (opcional)
        company_data: Datos de la empresa obtenidos de GlassdoorService
        question_count: Cantidad de preguntas a generar (default 5)
        
    Returns:
        Lista de diccionarios con preguntas estructuradas
    """
    try:
        try:
            from interview_data import (
                get_random_rrhh_questions,
                get_company_specific_questions,
            )
        except ImportError:
            from job_bot.interview_data import (
                get_random_rrhh_questions,
                get_company_specific_questions,
            )
        
        # 1. Obtener preguntas aleatorias del pool
        questions = get_random_rrhh_questions(question_count)
        
        # 2. Si hay empresa, reemplazar 1-2 preguntas por específicas
        if company_name:
            company_questions = get_company_specific_questions(company_name)
            if company_questions:
                # Reemplazar la última pregunta por una específica de la empresa
                questions[-1] = type(questions[0])(
                    id="company_specific",
                    category="company_research",
                    question=company_questions[0],
                    star_focus="Demostrar conocimiento real de la empresa y alineación con sus valores",
                    what_to_avoid="NO decir 'vi en la web que...' sin profundizar, NO ser superficial",
                    golden_tip="Investigá LinkedIn, noticias recientes, y conectá tu experiencia con sus desafíos actuales",
                    difficulty="medium"
                )
        
        # 3. Convertir a formato de retorno
        result = []
        for i, q in enumerate(questions, 1):
            result.append({
                "number": i,
                "id": q.id,
                "text": q.question,
                "category": q.category,
                "star_focus": q.star_focus,
                "what_to_avoid": q.what_to_avoid,
                "golden_tip": q.golden_tip,
                "difficulty": q.difficulty
            })
        
        return result
        
    except Exception as e:
        logger.error("Error generando preguntas RRHH: %s", e)
        return None


async def evaluate_rrhh_answer_star(
    question: str,
    answer: str,
    cv_text: str,
    star_focus: str,
    feedback_mode: str = "immediate"
) -> Optional[Dict]:
    """
    Evalúa una respuesta RRHH usando la metodología STAR estricta.
    
    Args:
        question: La pregunta realizada
        answer: Respuesta del candidato
        cv_text: CV para contexto
        star_focus: Qué aspectos STAR enfatizar para esta pregunta
        feedback_mode: "immediate" (corta) o "detailed" (más completa)
        
    Returns:
        Dict con evaluación estructurada o None si falla
    """
    if not config.GROQ_API_KEY:
        return None
    
    try:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=config.GROQ_API_KEY)
        
        # Prompt diferente según modo de feedback
        if feedback_mode == "immediate":
            prompt = f"""Sos un reclutador de RRHH senior evaluando respuestas usando el método STAR.
        
Pregunta: {question}
Respuesta del candidato: {answer}
Contexto CV: {cv_text[:1000]}
Enfoque para esta pregunta: {star_focus}

EVALUÁ usando el método STAR:
- S (Situation): ¿Describió claramente el contexto? ¿Quién? ¿Dónde? ¿Cuándo?
- T (Task): ¿Definió claramente su objetivo/desafío específico?
- A (Action): ¿Qué acciones tomó ÉL/ELLA específicamente (no el equipo)?
- R (Result): ¿Dio un resultado MEDIBLE con número/métrica?

Respondé en ESTE FORMATO EXACTO:

✅ S-Situación: [X]/10 - [feedback de 10 palabras máximo]
⚠️ T-Task: [X]/10 - [feedback de 10 palabras máximo]
✅ A-Acción: [X]/10 - [feedback de 10 palabras máximo]
❌ R-Resultado: [X]/10 - [feedback de 10 palabras máximo]

📊 Nota general: [X]/10

💡 Tip de Oro: [una oración con consejo específico para mejorar]

IMPORTANTE: Sé estricto. La mayoría de candidatos NO usan STAR bien. No des puntos por simpatía."""
        else:  # detailed
            prompt = f"""Sos un reclutador de RRHH senior evaluando respuestas usando el método STAR.
        
Pregunta: {question}
Respuesta del candidato: {answer}
Contexto CV: {cv_text[:1000]}
Enfoque para esta pregunta: {star_focus}

EVALUÁ usando el método STAR y dame un análisis detallado:

Para cada componente STAR:
1. S (Situation): ¿Contexto claro? ¿Específico o vago?
2. T (Task): ¿Objetivo definido? ¿Medible?
3. A (Action): ¿Qué hizo ÉL/ELLA (no el equipo)? ¿Detallado?
4. R (Result): ¿Métrica concreta? ¿Impacto cuantificado?

Respondé así:

<b>📊 NOTA GENERAL: [X]/10</b>

<b>🔍 ANÁLISIS STAR:</b>

✅ <b>S-Situación ([X]/10):</b>
[feedback detallado, 2-3 oraciones]

⚠️ <b>T-Task ([X]/10):</b>
[feedback detallado, 2-3 oraciones]

✅ <b>A-Acción ([X]/10):</b>
[feedback detallado, 2-3 oraciones]

❌ <b>R-Resultado ([X]/10):</b>
[feedback detallado, 2-3 oraciones]

<b>💡 Tip de Oro:</b>
[consejo específico y accionable]

<b>🎯 Para la próxima:</b>
[qué debería hacer diferente en la siguiente pregunta]"""
        
        chat_completion = await client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=config.GROQ_MODEL,
            temperature=0.3,  # Más bajo para ser más estricto y consistente
            max_tokens=800 if feedback_mode == "immediate" else 1200,
        )
        
        content = chat_completion.choices[0].message.content
        
        # Parsear la respuesta de la IA para extraer estructura
        result = parse_star_evaluation(content, feedback_mode)
        return result
        
    except Exception as e:
        logger.error("Error evaluando respuesta RRHH: %s", e)
        return None


def parse_star_evaluation(content: str, mode: str) -> Dict:
    """
    Parsea la evaluación de la IA para extraer scores estructurados.
    
    Args:
        content: Texto de respuesta de la IA
        mode: "immediate" o "detailed"
        
    Returns:
        Dict con estructura parseada
    """
    import re
    
    result = {
        "overall_score": 0,
        "overall_feedback": "",
        "star_breakdown": {
            "Situation": {"score": 0, "feedback": ""},
            "Task": {"score": 0, "feedback": ""},
            "Action": {"score": 0, "feedback": ""},
            "Result": {"score": 0, "feedback": ""}
        },
        "golden_tip": "",
        "raw_text": content
    }
    
    try:
        # Extraer nota general
        overall_match = re.search(r'Nota general:?\s*(\d+(?:\.\d+)?)/10', content, re.IGNORECASE)
        if overall_match:
            result["overall_score"] = float(overall_match.group(1))
        
        # Extraer componentes STAR
        patterns = {
            "Situation": r'[S\-]\s*Situaci[oó]n:?\s*(\d+(?:\.\d+)?)/?\d*\s*[-:]?\s*([^\n]+)',
            "Task": r'[T\-]\s*Task:?\s*(\d+(?:\.\d+)?)/?\d*\s*[-:]?\s*([^\n]+)',
            "Action": r'[A\-]\s*Acci[oó]n:?\s*(\d+(?:\.\d+)?)/?\d*\s*[-:]?\s*([^\n]+)',
            "Result": r'[R\-]\s*Resultado:?\s*(\d+(?:\.\d+)?)/?\d*\s*[-:]?\s*([^\n]+)'
        }
        
        for component, pattern in patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                result["star_breakdown"][component]["score"] = float(match.group(1))
                result["star_breakdown"][component]["feedback"] = match.group(2).strip()
        
        # Extraer tip de oro
        tip_match = re.search(r'Tip de [Oo]ro:?\s*([^\n]+(?:\n[^\n]+)?)', content)
        if tip_match:
            result["golden_tip"] = tip_match.group(1).strip()
        
        # Calcular overall si no lo tenemos pero tenemos componentes
        if result["overall_score"] == 0:
            scores = [v["score"] for v in result["star_breakdown"].values() if v["score"] > 0]
            if scores:
                result["overall_score"] = round(sum(scores) / len(scores), 1)
        
    except Exception as e:
        logger.error("Error parseando evaluación STAR: %s", e)
        # Si falla el parseo, devolver el texto crudo
        result["overall_feedback"] = content
    
    return result


def format_star_feedback(evaluation: Dict, mode: str = "immediate") -> str:
    """
    Formatea la evaluación STAR para mostrar al usuario.
    
    Args:
        evaluation: Dict de evaluate_rrhh_answer_star
        mode: "immediate" o "detailed"
        
    Returns:
        Texto formateado para Telegram
    """
    if not evaluation:
        return "⚠️ No pude evaluar esta respuesta."
    
    # Si tiene raw_text pero no estructura parseada, devolver raw
    if evaluation.get("raw_text") and not evaluation.get("overall_score"):
        return evaluation["raw_text"]
    
    star = evaluation["star_breakdown"]
    
    if mode == "immediate":
        lines = [
            f"<b>📝 Feedback:</b>\n",
            f"✅ S-Situación: {star['Situation']['score']}/10 - {star['Situation']['feedback']}",
            f"⚠️ T-Task: {star['Task']['score']}/10 - {star['Task']['feedback']}",
            f"✅ A-Acción: {star['Action']['score']}/10 - {star['Action']['feedback']}",
            f"❌ R-Resultado: {star['Result']['score']}/10 - {star['Result']['feedback']}",
            f"",
            f"📊 <b>Nota: {evaluation['overall_score']}/10</b>",
            f"",
            f"💡 <b>Tip de Oro:</b> {evaluation['golden_tip']}"
        ]
    else:  # detailed
        lines = [
            f"<b>📊 NOTA GENERAL: {evaluation['overall_score']}/10</b>\n",
            f"<b>🔍 ANÁLISIS STAR:</b>\n",
            f"✅ <b>S-Situación ({star['Situation']['score']}/10):</b> {star['Situation']['feedback']}",
            f"⚠️ <b>T-Task ({star['Task']['score']}/10):</b> {star['Task']['feedback']}",
            f"✅ <b>A-Acción ({star['Action']['score']}/10):</b> {star['Action']['feedback']}",
            f"❌ <b>R-Resultado ({star['Result']['score']}/10):</b> {star['Result']['feedback']}",
            f"",
            f"💡 <b>Tip de Oro:</b> {evaluation['golden_tip']}",
        ]
    
    return "\n".join(lines)

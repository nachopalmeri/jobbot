import os
import re
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
import httpx
from pydantic import BaseModel

try:
    from job_bot.cv_analyzer import compare_cv_with_offer, extract_keywords, parse_cv
    from job_bot.database import Database
except ImportError:
    from cv_analyzer import compare_cv_with_offer, extract_keywords, parse_cv
    from database import Database

from .auth import get_authenticated_user, get_db


router = APIRouter()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"


class CVAnalysisRequest(BaseModel):
    job_url: str
    job_description: Optional[str] = None
    user_cv: Optional[str] = None


class CVProposalRequest(BaseModel):
    job_url: str
    job_title: str
    company_name: str
    job_description: Optional[str] = None
    user_cv: Optional[str] = None


SECTION_PATTERNS = {
    "contact": [r"@", r"\+?\d[\d\s().-]{7,}", r"linkedin", r"github"],
    "summary": [r"\bsummary\b", r"\bperfil\b", r"\babout\b", r"\bresumen\b"],
    "experience": [r"\bexperience\b", r"\bexperiencia\b", r"\bwork\b"],
    "education": [r"\beducation\b", r"\beducaci[oó]n\b", r"\bestudios\b"],
    "skills": [r"\bskills\b", r"\bhabilidades\b", r"\btecnolog", r"\bstack\b"],
}

ACTION_VERBS = {
    "built",
    "created",
    "improved",
    "led",
    "launched",
    "optimized",
    "reduced",
    "increased",
    "implemented",
    "developed",
    "designed",
    "automated",
    "migrated",
    "managed",
    "collaborated",
}


async def analyze_with_groq(prompt: str) -> str:
    if not GROQ_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio de IA no disponible temporalmente",
        )

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "Eres un experto en recursos humanos y analisis de CVs.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 1024,
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=data,
            )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo completar el analisis",
        ) from exc

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo completar el analisis",
        )
    return response.json()["choices"][0]["message"]["content"]


def _consume_ai_quota(db: Database, telegram_id: int):
    if not db.check_usage_limit(telegram_id, "ai_analyses"):
        raise HTTPException(
            status_code=403,
            detail="Limite de analisis alcanzado para tu plan actual",
        )
    db.increment_usage(telegram_id, "ai_analyses")


def _clean_text(value: str | None) -> str:
    return (value or "").strip()


def _extract_uploaded_cv_text(file: UploadFile | None) -> str:
    if not file or not file.filename:
        return ""

    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".pdf", ".txt"}:
        raise HTTPException(
            status_code=400,
            detail="Solo se admiten CVs en formato PDF o TXT",
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name

    try:
        parsed = parse_cv(tmp_path)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    if not parsed:
        raise HTTPException(status_code=400, detail="No se pudo leer el contenido del CV")

    return parsed


def _detect_sections(cv_text: str) -> dict[str, bool]:
    text = cv_text.lower()
    return {
        section: any(re.search(pattern, text) for pattern in patterns)
        for section, patterns in SECTION_PATTERNS.items()
    }


def _extract_quick_wins(cv_text: str, sections: dict[str, bool]) -> list[str]:
    quick_wins: list[str] = []
    if not sections["summary"]:
        quick_wins.append("Agregá un resumen profesional corto al inicio para contextualizar tu perfil.")
    if not sections["skills"]:
        quick_wins.append("Incluí una sección de skills explícita con tus tecnologías clave.")
    if not re.search(r"\d+[%+]", cv_text):
        quick_wins.append("Sumá métricas concretas: impacto, % de mejora, tiempos o volumen.")
    if "linkedin" not in cv_text.lower():
        quick_wins.append("Añadí tu LinkedIn para reforzar credibilidad y contexto profesional.")
    return quick_wins[:4]


def _score_cv_quality(cv_text: str) -> dict:
    sections = _detect_sections(cv_text)
    word_count = len(re.findall(r"\b\w+\b", cv_text))
    keyword_count = len(extract_keywords(cv_text)["tech"])
    action_verb_hits = sum(1 for verb in ACTION_VERBS if re.search(rf"\b{re.escape(verb)}\b", cv_text.lower()))
    metric_hits = len(re.findall(r"\b\d+(?:[%+]|k\b|m\b)?", cv_text.lower()))

    score = 0
    score += 18 if sections["contact"] else 0
    score += 14 if sections["summary"] else 0
    score += 18 if sections["experience"] else 0
    score += 12 if sections["education"] else 0
    score += 16 if sections["skills"] else 0
    score += 10 if 180 <= word_count <= 950 else 4
    score += min(6, action_verb_hits * 2)
    score += min(6, metric_hits * 2)

    strengths: list[str] = []
    if sections["contact"]:
        strengths.append("Tus datos de contacto parecen estar presentes.")
    if sections["experience"]:
        strengths.append("El CV muestra experiencia profesional identificable.")
    if sections["skills"]:
        strengths.append("Hay una base técnica reconocible para matching ATS.")
    if metric_hits >= 2:
        strengths.append("Ya usás métricas, algo valioso para recruiters y ATS.")

    return {
        "ats_score": min(score, 100),
        "sections": sections,
        "word_count": word_count,
        "keyword_count": keyword_count,
        "action_verb_hits": action_verb_hits,
        "metric_hits": metric_hits,
        "strengths": strengths[:4],
        "quick_wins": _extract_quick_wins(cv_text, sections),
    }


def _quota_snapshot(db: Database, telegram_id: int) -> dict:
    web_user = db.get_web_user(telegram_id) or {}
    ai_used = int(web_user.get("ai_analyses_used") or 0)
    ai_limit = int(web_user.get("ai_analyses_limit") or 0)
    return {
        "used": ai_used,
        "limit": ai_limit,
        "remaining": max(0, ai_limit - ai_used),
        "ai_enabled": ai_limit > 0,
    }


def _load_saved_cv_text(current_user: dict) -> str:
    stored_path = (current_user.get("user") or {}).get("cv_path")
    if not stored_path:
        return ""

    try:
      return parse_cv(stored_path) or ""
    except Exception:
      return ""


@router.post("/scan")
async def scan_cv(
    cv_file: UploadFile | None = File(default=None),
    cv_text: str = Form(default=""),
    job_description: str = Form(default=""),
    job_title: str = Form(default=""),
    company_name: str = Form(default=""),
    mode: str = Form(default="basic"),  # 'basic' o 'pro'
    current_user: dict = Depends(get_authenticated_user),
    db: Database = Depends(get_db),
):
    """
    Analiza un CV. 
    - mode='basic': Análisis ATS gratuito (siempre disponible)
    - mode='pro': Incluye análisis IA (consume 1 crédito o usa límite del plan)
    """
    uploaded_text = _extract_uploaded_cv_text(cv_file)
    final_cv_text = _clean_text(cv_text) or uploaded_text
    final_job_description = _clean_text(job_description)
    final_job_title = _clean_text(job_title)
    final_company_name = _clean_text(company_name)

    if not final_cv_text:
        raise HTTPException(status_code=400, detail="Necesitamos el texto o archivo de tu CV")

    # Score básico siempre disponible
    quality = _score_cv_quality(final_cv_text)
    comparison = (
        compare_cv_with_offer(final_cv_text, final_job_description)
        if final_job_description
        else None
    )
    
    # Determinar si puede usar análisis IA
    telegram_id = current_user["telegram_id"]
    quota = _quota_snapshot(db, telegram_id)
    credits_balance = db.get_user_credits_balance(telegram_id)
    
    ai_feedback = None
    consumed_ai = False
    used_credits = False
    
    if mode == "pro":
        # Intentar usar créditos primero, luego límite del plan
        has_credits = credits_balance["total_credits"] > 0
        has_plan_quota = quota["ai_enabled"] and db.check_usage_limit(telegram_id, "ai_analyses")
        
        if has_credits:
            # Consumir crédito
            consume_result = db.consume_credits(
                telegram_id=telegram_id,
                credits_to_consume=1,
                description=f"CV Analysis Pro: {final_job_title or 'General'}",
                related_entity_type="cv_scan",
                related_entity_id=None
            )
            if consume_result["success"]:
                used_credits = True
            else:
                raise HTTPException(
                    status_code=403,
                    detail="No se pudieron consumir créditos. Intenta nuevamente."
                )
        elif has_plan_quota:
            # Usar límite del plan (Pro/Premium)
            _consume_ai_quota(db, telegram_id)
        else:
            # Sin créditos ni plan
            if credits_balance["unlock_active"]:
                raise HTTPException(
                    status_code=403,
                    detail="Te quedaste sin créditos. Comprá más en /dashboard/creditos"
                )
            else:
                raise HTTPException(
                    status_code=403,
                    detail="Análisis Pro requiere créditos o Plan Pro/Premium. Desbloqueá CV Suite en /dashboard/creditos"
                )
        
        # Generar feedback IA
        prompt = f"""
Analizá este CV como si fueras una mezcla de ATS + recruiter.

Objetivo:
- dar feedback corto, accionable y brutalmente claro
- priorizar impacto, legibilidad, keywords y ajuste al puesto
- responder en español

Puesto objetivo: {final_job_title or "No especificado"}
Empresa objetivo: {final_company_name or "No especificada"}
Job description:
{final_job_description or "No provista"}

CV:
{final_cv_text[:5000]}

Devolvé:
1. Diagnóstico general en 2-3 líneas
2. 3 mejoras prioritarias
3. Una recomendación final sobre si este CV está listo para aplicar hoy
"""
        ai_feedback = await analyze_with_groq(prompt)
        db.record_ai_analysis(telegram_id, cv_analyzed=True, job_matched=bool(final_job_description))
        quota = _quota_snapshot(db, telegram_id)
        consumed_ai = True
        
        # Actualizar balance de créditos si se usaron
        if used_credits:
            credits_balance = db.get_user_credits_balance(telegram_id)

    return {
        "job_title": final_job_title,
        "company_name": final_company_name,
        "mode": mode,
        "ats_score": quality["ats_score"],
        "match_score": comparison["score"] if comparison else None,
        "matching_keywords": comparison["matching"] if comparison else [],
        "missing_keywords": comparison["missing"] if comparison else [],
        "extra_keywords": comparison["extra"] if comparison else quality["strengths"],
        "suggestions": comparison["suggestions"] if comparison else quality["quick_wins"],
        "strengths": quality["strengths"],
        "sections": quality["sections"],
        "metrics": {
            "word_count": quality["word_count"],
            "keyword_count": quality["keyword_count"],
            "action_verb_hits": quality["action_verb_hits"],
            "metric_hits": quality["metric_hits"],
        },
        "quota": quota,
        "credits": {
            "total": credits_balance["total_credits"],
            "unlock_active": credits_balance["unlock_active"],
        } if mode == "pro" else None,
        "ai_feedback": ai_feedback,
        "ai_feedback_included": consumed_ai,
        "used_credits": used_credits,
    }


@router.post("/analyze")
async def analyze_cv(
    request: CVAnalysisRequest,
    current_user: dict = Depends(get_authenticated_user),
    db: Database = Depends(get_db),
):
    if current_user["plan"] not in {"pro", "premium"}:
        raise HTTPException(
            status_code=403,
            detail="Esta funcion requiere Plan Pro",
        )

    _consume_ai_quota(db, current_user["telegram_id"])

    user_cv = _clean_text(request.user_cv) or _load_saved_cv_text(current_user)
    if not user_cv:
        raise HTTPException(
            status_code=400,
            detail="Necesitamos tu CV para analizar el match contra la oferta",
        )

    local_analysis = compare_cv_with_offer(user_cv, request.job_description or request.job_url)
    prompt = f"""
Analizá el siguiente CV contra la oferta. No seas vago ni genérico.

Oferta:
- URL: {request.job_url}
- Descripción: {request.job_description or "No proporcionada"}

CV del candidato:
{user_cv}

Señales calculadas localmente:
- Match score: {local_analysis["score"]}%
- Keywords que coinciden: {", ".join(local_analysis["matching"]) or "Ninguna clara"}
- Keywords faltantes: {", ".join(local_analysis["missing"]) or "No detectadas"}
- Posibles alertas: {", ".join(local_analysis["penalties"]) or "Sin alertas duras"}

Devolvé:
1. Diagnóstico corto y honesto
2. Qué sí encaja del CV con la oferta
3. Qué está faltando o queda flojo
4. Recomendación final: aplicar ahora, aplicar ajustando CV, o no priorizar esta oferta
"""

    analysis = await analyze_with_groq(prompt)
    db.record_ai_analysis(current_user["telegram_id"], cv_analyzed=True, job_matched=True)

    return {
        "job_url": request.job_url,
        "analysis": analysis,
        "match_score": local_analysis["score"],
        "matching_keywords": local_analysis["matching"],
        "missing_keywords": local_analysis["missing"],
        "penalties": local_analysis["penalties"],
    }


@router.post("/proposal")
async def generate_proposal(
    request: CVProposalRequest,
    current_user: dict = Depends(get_authenticated_user),
    db: Database = Depends(get_db),
):
    if current_user["plan"] != "premium":
        raise HTTPException(
            status_code=403,
            detail="CV Tailoring requiere Plan Premium",
        )

    _consume_ai_quota(db, current_user["telegram_id"])
    user_cv = _clean_text(request.user_cv) or _load_saved_cv_text(current_user)
    if not user_cv:
        raise HTTPException(
            status_code=400,
            detail="Necesitamos el texto de tu CV o uno cargado previamente en JobBot",
        )

    local_analysis = compare_cv_with_offer(
        user_cv,
        " ".join(
            value for value in [request.job_title, request.company_name, request.job_description or ""]
            if value
        ),
    )
    prompt = f"""
Escribí una cover letter breve y creíble para esta vacante.

Contexto del puesto:
- Empresa: {request.company_name}
- Puesto: {request.job_title}
- URL: {request.job_url}
- Descripción: {request.job_description or "No provista"}

CV del candidato:
{user_cv}

Señales de match:
- Match score local: {local_analysis["score"]}%
- Coincidencias: {", ".join(local_analysis["matching"]) or "Sin coincidencias fuertes"}
- Faltantes: {", ".join(local_analysis["missing"]) or "No detectados"}
- Alertas: {", ".join(local_analysis["penalties"]) or "Sin alertas duras"}

Instrucciones:
1. Máximo 220 palabras.
2. 3 párrafos.
3. No inventes experiencia ni tecnologías.
4. Mencioná solo fortalezas respaldadas por el CV.
5. Si faltan detalles de la oferta, mantené la carta sobria y específica al rol, sin humo.
6. Cerrá con una línea breve de interés genuino.
"""

    proposal = await analyze_with_groq(prompt)
    db.record_ai_analysis(current_user["telegram_id"], cv_analyzed=True, job_matched=False)

    return {
        "company": request.company_name,
        "job_title": request.job_title,
        "proposal": proposal,
        "copied_text": proposal,
    }


@router.get("/tips/{job_id}")
async def get_application_tips(
    job_id: str,
    _: dict = Depends(get_authenticated_user),
):
    return {
        "job_id": job_id,
        "tips": [
            {
                "title": "Aplica temprano",
                "description": "Los primeros aplicantes tienen mas chances de ser vistos.",
                "priority": "high",
            },
            {
                "title": "Personaliza el asunto",
                "description": "Usa el nombre del puesto en el asunto del email.",
                "priority": "high",
            },
            {
                "title": "Sigue up",
                "description": "Haz un follow-up educado si no recibes respuesta.",
                "priority": "low",
            },
        ],
    }


@router.post("/mock-interview")
async def start_mock_interview(
    job_title: str,
    current_user: dict = Depends(get_authenticated_user),
    db: Database = Depends(get_db),
):
    if current_user["plan"] != "premium":
        raise HTTPException(
            status_code=403,
            detail="Entrevistas mock requieren Plan Premium",
        )

    if not db.check_usage_limit(current_user["telegram_id"], "interviews"):
        raise HTTPException(
            status_code=403,
            detail="Alcanzaste el limite mensual de mock interviews para tu plan actual",
        )

    db.increment_usage(current_user["telegram_id"], "interviews")

    questions = {
        "Frontend Developer": [
            "Cuentame sobre un proyecto desafiante con React que hayas liderado",
            "Como manejas el estado en aplicaciones grandes",
            "Cual es tu approach para optimizar performance",
        ],
        "Default": [
            "Cuentame sobre vos y tu experiencia",
            "Por que te interesa este puesto",
            "Cuales son tus fortalezas y debilidades",
        ],
    }

    return {
        "job_title": job_title,
        "questions": questions.get(job_title, questions["Default"]),
    }


@router.get("/history")
async def get_cv_history(
    limit: int = 50,
    current_user: dict = Depends(get_authenticated_user),
    db: Database = Depends(get_db),
):
    """
    Obtiene el historial de análisis de CV del usuario.
    Requiere CV Suite Unlock para acceder al historial completo.
    """
    telegram_id = current_user.get("telegram_id")
    if not telegram_id:
        raise HTTPException(status_code=400, detail="Usuario sin telegram_id")
    
    # Verificar acceso al historial
    credits = db.get_user_credits_balance(telegram_id)
    if not credits["unlock_active"]:
        raise HTTPException(
            status_code=403,
            detail="Desbloqueá CV Suite para ver tu historial completo en /dashboard/creditos"
        )
    
    # Obtener análisis de la tabla ai_analyses
    if db.db_type == "supabase":
        query = """
            SELECT id, cv_analyzed, job_matched, prompt_tokens, response_tokens, created_at
            FROM ai_analyses
            WHERE telegram_id = %s AND cv_analyzed = 1
            ORDER BY created_at DESC
            LIMIT %s
        """
    else:
        query = """
            SELECT id, cv_analyzed, job_matched, prompt_tokens, response_tokens, created_at
            FROM ai_analyses
            WHERE telegram_id = ? AND cv_analyzed = 1
            ORDER BY created_at DESC
            LIMIT ?
        """
    
    rows = db._fetchall(query, (telegram_id, limit))
    
    history = []
    for row in rows:
        history.append({
            "id": row["id"],
            "type": "cv_analysis",
            "has_job_match": bool(row["job_matched"]),
            "tokens_used": (row["prompt_tokens"] or 0) + (row["response_tokens"] or 0),
            "created_at": row["created_at"],
        })
    
    return {
        "history": history,
        "count": len(history),
        "unlock_active": credits["unlock_active"],
    }


@router.get("/history/{analysis_id}")
async def get_cv_analysis_detail(
    analysis_id: int,
    current_user: dict = Depends(get_authenticated_user),
    db: Database = Depends(get_db),
):
    """Obtiene el detalle de un análisis específico."""
    telegram_id = current_user.get("telegram_id")
    if not telegram_id:
        raise HTTPException(status_code=400, detail="Usuario sin telegram_id")
    
    # Verificar acceso
    credits = db.get_user_credits_balance(telegram_id)
    if not credits["unlock_active"]:
        raise HTTPException(
            status_code=403,
            detail="Desbloqueá CV Suite para ver detalles en /dashboard/creditos"
        )
    
    # Obtener el análisis específico
    if db.db_type == "supabase":
        query = """
            SELECT id, cv_analyzed, job_matched, prompt_tokens, response_tokens, created_at
            FROM ai_analyses
            WHERE id = %s AND telegram_id = %s
        """
    else:
        query = """
            SELECT id, cv_analyzed, job_matched, prompt_tokens, response_tokens, created_at
            FROM ai_analyses
            WHERE id = ? AND telegram_id = ?
        """
    
    row = db._fetchone(query, (analysis_id, telegram_id))
    
    if not row:
        raise HTTPException(status_code=404, detail="Análisis no encontrado")
    
    return {
        "id": row["id"],
        "type": "cv_analysis",
        "has_job_match": bool(row["job_matched"]),
        "prompt_tokens": row["prompt_tokens"],
        "response_tokens": row["response_tokens"],
        "total_tokens": (row["prompt_tokens"] or 0) + (row["response_tokens"] or 0),
        "created_at": row["created_at"],
    }

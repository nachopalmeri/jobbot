import os
import re
from pathlib import Path
from time import time
from typing import Optional

import requests
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel

try:
    from job_bot.database import Database
    from job_bot import config
    from job_bot.cv_analyzer import extract_keywords, parse_cv
except ImportError:
    from database import Database
    import config
    from cv_analyzer import extract_keywords, parse_cv

from .auth import get_authenticated_user, get_db
from ..core.cache import cache, user_dashboard_key


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
    user_cv: Optional[str] = None


def _resolve_user_cv_text(db: Database, telegram_id: int, provided_cv: Optional[str]) -> str:
    if provided_cv and provided_cv.strip():
        return provided_cv.strip()

    user = db.get_user(telegram_id) or {}
    cv_path = user.get("cv_path")
    if not cv_path:
        raise HTTPException(
            status_code=400,
            detail="No hay CV cargado. Subí uno desde el dashboard o enviá el texto manualmente.",
        )

    parsed = parse_cv(cv_path)
    if not parsed:
        raise HTTPException(
            status_code=400,
            detail="No pude leer tu CV guardado. Probá volver a subirlo.",
        )
    return parsed


def _safe_filename(original_name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]", "_", original_name or "cv.pdf")
    return cleaned[:120] or "cv.pdf"


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

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=data,
        timeout=30,
    )
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

    user_cv = _resolve_user_cv_text(db, current_user["telegram_id"], request.user_cv)

    prompt = f"""
Analiza el siguiente CV contra la descripcion del empleo:

URL del empleo: {request.job_url}

Descripcion del empleo:
{request.job_description or "No proporcionada"}

CV del candidato:
{user_cv}

Proporciona:
1. Lista de keywords que matchean
2. Keywords faltantes
3. Score de match (0-100%)
4. Recomendaciones especificas para mejorar
"""

    analysis = await analyze_with_groq(prompt)
    db.record_ai_analysis(current_user["telegram_id"], cv_analyzed=True, job_matched=True)

    return {
        "job_url": request.job_url,
        "analysis": analysis,
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

    user_cv = _resolve_user_cv_text(db, current_user["telegram_id"], request.user_cv)

    prompt = f"""
Genera una propuesta personalizada para el siguiente empleo:

Empresa: {request.company_name}
Puesto: {request.job_title}

CV del candidato:
{user_cv}

La propuesta debe:
1. Ser de 2-3 parrafos maximo
2. Destacar la experiencia relevante
3. Ser personalizada y profesional
4. Incluir un llamado a la accion claro
"""

    proposal = await analyze_with_groq(prompt)
    db.record_ai_analysis(current_user["telegram_id"], cv_analyzed=True, job_matched=False)

    return {
        "company": request.company_name,
        "job_title": request.job_title,
        "proposal": proposal,
        "copied_text": proposal,
    }


@router.post("/upload")
async def upload_cv(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_authenticated_user),
    db: Database = Depends(get_db),
):
    content_type = (file.content_type or "").lower()
    allowed_types = {
        "application/pdf": ".pdf",
        "text/plain": ".txt",
    }
    extension = Path(file.filename or "").suffix.lower()
    if content_type in allowed_types:
        extension = allowed_types[content_type]

    if extension not in {".pdf", ".txt"}:
        raise HTTPException(
            status_code=400,
            detail="Solo se permiten archivos PDF o TXT para el CV.",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="El archivo está vacío.")
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="El CV supera el límite de 5MB.")

    storage_dir = Path(config.CV_STORAGE_PATH)
    if not storage_dir.is_absolute():
        storage_dir = Path.cwd() / storage_dir
    storage_dir.mkdir(parents=True, exist_ok=True)

    safe_name = _safe_filename(file.filename or f"cv{extension}")
    target_name = f"{current_user['telegram_id']}_{int(time())}_{safe_name}"
    target_path = storage_dir / target_name
    target_path.write_bytes(content)

    db.create_user_if_not_exists(current_user["telegram_id"], current_user["name"])
    db.set_user_cv(current_user["telegram_id"], str(target_path))
    cache.delete("users", user_dashboard_key(current_user["telegram_id"]))

    parsed = parse_cv(str(target_path))
    if not parsed:
        raise HTTPException(
            status_code=400,
            detail="El archivo se guardó, pero no pude extraer texto útil del CV.",
        )

    keywords = extract_keywords(parsed)
    return {
        "ok": True,
        "file_name": safe_name,
        "cv_uploaded": True,
        "top_keywords": keywords.get("tech", [])[:8],
        "message": "CV cargado correctamente",
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
):
    if current_user["plan"] != "premium":
        raise HTTPException(
            status_code=403,
            detail="Entrevistas mock requieren Plan Premium",
        )

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

import os
from typing import Optional

import requests
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

try:
    from job_bot.database import Database
except ImportError:
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
    user_cv: str


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

    prompt = f"""
Analiza el siguiente CV contra la descripcion del empleo:

URL del empleo: {request.job_url}

Descripcion del empleo:
{request.job_description or "No proporcionada"}

CV del candidato:
{request.user_cv or "No proporcionado"}

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

    prompt = f"""
Genera una propuesta personalizada para el siguiente empleo:

Empresa: {request.company_name}
Puesto: {request.job_title}

CV del candidato:
{request.user_cv}

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

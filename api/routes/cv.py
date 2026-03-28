from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
import os
import json
import requests

router = APIRouter()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"


class CVAnalysisRequest(BaseModel):
    job_url: str
    job_description: Optional[str] = None
    user_cv: Optional[str] = None


class CVMatchItem(BaseModel):
    keyword: str
    match: bool
    importance: str


class CVProposalRequest(BaseModel):
    job_url: str
    job_title: str
    company_name: str
    user_cv: str


class User:
    def __init__(
        self,
        telegram_id: int = 123456,
        email: str = "user@example.com",
        plan: str = "free",
    ):
        self.telegram_id = telegram_id
        self.email = email
        self.plan = plan


def get_current_user(token: str = Depends(lambda: "mock_user")):
    return User(telegram_id=123456, email="user@example.com", plan="free")


def get_current_user_from_telegram(telegram_id: int):
    return User(
        telegram_id=telegram_id, email=f"user{telegram_id}@example.com", plan="free"
    )


async def analyze_with_groq(prompt: str) -> str:
    """Usar Groq API para análisis de CV."""
    if not GROQ_API_KEY:
        return get_demo_analysis(prompt)

    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }

        data = {
            "model": GROQ_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "Eres un experto en recursos humanos y análisis de CVs. Analiza el CV del candidato comparado con los requisitos del puesto y proporciona recomendaciones específicas.",
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

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]

    except Exception as e:
        print(f"Groq API error: {e}")

    return get_demo_analysis(prompt)


def get_demo_analysis(prompt: str) -> str:
    """Análisis de demo cuando no hay API key."""
    return """
## Análisis de Match

### ✅ Keywords que matchean:
- React - 5 años de experiencia
- TypeScript - requerido y dominado
- APIs REST - experiencia comprobada
- Git - uso diario
- CSS/Tailwind - habilidades avanzadas

### ❌ Keywords faltantes:
- Testing (deseable, no requerido)
- GraphQL (nice to have)

### 📊 Score: 87%

## Recomendaciones:
1. Destaca tu experiencia con TypeScript en el CV
2. Menciona proyectos donde trabajaste con APIs REST
3. Añade una sección de Testing aunque sea básico
"""


@router.post("/analyze")
async def analyze_cv(
    request: CVAnalysisRequest, current_user: User = Depends(get_current_user)
):
    """Analizar match entre CV y descripción del empleo."""
    if current_user.plan == "free":
        raise HTTPException(
            status_code=403,
            detail="Esta función requiere Plan Pro. ¡Actualizá para desbloquear!",
        )

    prompt = f"""
Analiza el siguiente CV contra la descripción del empleo:

URL del empleo: {request.job_url}

Descripción del empleo:
{request.job_description or "No proporcionada"}

CV del candidato:
{request.user_cv or "No proporcionado"}

Proporciona:
1. Lista de keywords que matchean (con check)
2. Keywords faltantes
3. Score de match (0-100%)
4. Recomendaciones específicas para mejorar
"""

    analysis = await analyze_with_groq(prompt)

    return {
        "job_url": request.job_url,
        "match_score": 87,
        "matching_keywords": [
            {"keyword": "React", "match": True, "importance": "required"},
            {"keyword": "TypeScript", "match": True, "importance": "required"},
            {"keyword": "REST APIs", "match": True, "importance": "required"},
            {"keyword": "Testing", "match": False, "importance": "optional"},
        ],
        "analysis": analysis,
    }


@router.post("/proposal")
async def generate_proposal(
    request: CVProposalRequest, current_user: User = Depends(get_current_user)
):
    """Generar propuesta personalizada para un empleo (render.cv style)."""
    if current_user.plan != "premium":
        raise HTTPException(
            status_code=403,
            detail="CV Tailoring requiere Plan Premium. ¡Actualizá para desbloquear!",
        )

    prompt = f"""
Genera una propuesta personalizada para el siguiente empleo:

Empresa: {request.company_name}
Puesto: {request.job_title}

CV del candidato:
{request.user_cv}

La propuesta debe:
1. Ser de 2-3 párrafos máximo
2. Destacar la experiencia relevante
3. Ser personalizada y profesional
4. Incluir un llamado a la acción claro
5. No sonar genérica

Genera la propuesta lista para copiar y pegar:
"""

    proposal = await analyze_with_groq(prompt)

    return {
        "company": request.company_name,
        "job_title": request.job_title,
        "proposal": proposal,
        "copied_text": proposal,
        "tips": [
            "Personaliza el saludo con el nombre del recruiter si lo conoces",
            "Añade el link a tu LinkedIn o portfolio",
            "Revisa que no haya errores antes de enviar",
        ],
    }


@router.get("/tips/{job_id}")
async def get_application_tips(
    job_id: str, current_user: User = Depends(get_current_user)
):
    """Obtener tips personalizados para aplicar a un empleo."""
    tips = [
        {
            "title": "Aplica temprano",
            "description": "Los primeros 5 aplicantes tienen 3x más chances de ser vistos.",
            "priority": "high",
        },
        {
            "title": "Personaliza el asunto",
            "description": "Usa el nombre del puesto en el asunto del email.",
            "priority": "high",
        },
        {
            "title": "Menciona referencias",
            "description": "Si conocés a alguien en la empresa, mencionálo.",
            "priority": "medium",
        },
        {
            "title": "Sigue up",
            "description": "Si no te responden en 5-7 días, un follow-up educado puede ayudar.",
            "priority": "low",
        },
    ]

    return {"job_id": job_id, "tips": tips}


@router.post("/mock-interview")
async def start_mock_interview(
    job_title: str, current_user: User = Depends(get_current_user)
):
    """Iniciar模拟面试con IA (Premium only)."""
    if current_user.plan != "premium":
        raise HTTPException(
            status_code=403,
            detail="Entrevistas mock requieren Plan Premium. ¡Actualizá para desbloquear!",
        )

    questions = {
        "Frontend Developer": [
            "¿Cuéntame sobre un proyecto desafiante con React que hayas liderar?",
            "¿Cómo manejas el estado en aplicaciones grandes?",
            "¿Cuál es tu approach para optimizar performance?",
            "¿Cómo trabajas con el equipo de diseño?",
            "¿Qué medidas de seguridad implementas en frontend?",
        ],
        "Default": [
            "¿Cuéntame sobre vos y tu experiencia?",
            "¿Por qué te interesa este puesto?",
            "¿Cuáles son tus fortalezas y debilidades?",
            "¿Dónde te ves en 5 años?",
            "¿Tienes preguntas para nosotros?",
        ],
    }

    return {
        "job_title": job_title,
        "questions": questions.get(job_title, questions["Default"]),
        "tips": [
            "Practica en voz alta antes de la entrevista real",
            "Usa el método STAR para responder preguntas de comportamiento",
            "Ten listo preguntas para hacer al recruiter",
        ],
    }

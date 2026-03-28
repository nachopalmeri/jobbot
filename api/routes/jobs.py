from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List

router = APIRouter()


def get_current_user(token: str = Depends(lambda: "mock_user")):
    return {"telegram_id": 123456, "email": "user@example.com", "plan": "free"}


@router.get("/search")
async def search_jobs(
    q: str = Query(..., description="Query de búsqueda"),
    modality: Optional[str] = Query(None, description="remote, hybrid, onsite"),
    location: Optional[str] = Query(None, description="Ubicación"),
    current_user=Depends(get_current_user),
):
    """Buscar empleos - placeholder integrando con scraper real."""
    return {
        "jobs": [
            {
                "id": 1,
                "title": "Python Developer",
                "company": "Tech Corp",
                "location": "Remote",
                "modality": "remote",
                "source": "Remotive",
                "url": "https://example.com/job/1",
                "salary": "$80,000 - $120,000",
                "posted_at": "2026-03-28",
            },
            {
                "id": 2,
                "title": "Backend Engineer",
                "company": "StartupXYZ",
                "location": "Buenos Aires",
                "modality": "hybrid",
                "source": "LinkedIn",
                "url": "https://example.com/job/2",
                "salary": "$50,000 - $80,000",
                "posted_at": "2026-03-27",
            },
        ],
        "total": 2,
        "query": q,
    }


@router.get("/recommended")
async def get_recommended_jobs(current_user=Depends(get_current_user)):
    """Obtener empleos recomendados basado en perfil."""
    return {"jobs": [], "message": "Configura tu perfil para ver recomendaciones"}


@router.post("/track")
async def track_application(
    job_title: str,
    company: str,
    url: str,
    notes: Optional[str] = None,
    current_user=Depends(get_current_user),
):
    """Registrar postulación para tracking."""
    return {
        "id": 123,
        "job_title": job_title,
        "company": company,
        "url": url,
        "status": "aplicado",
        "applied_at": "2026-03-28",
    }


@router.get("/applications")
async def get_applications(current_user=Depends(get_current_user)):
    """Obtener todas las postulaciones del usuario."""
    return {"applications": []}


@router.patch("/applications/{app_id}")
async def update_application(
    app_id: int, status: str, current_user=Depends(get_current_user)
):
    """Actualizar estado de una postulación."""
    return {"id": app_id, "status": status, "message": "Estado actualizado"}

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

router = APIRouter()


def get_current_user(token: str = Depends(lambda: "mock_user")):
    """Placeholder - implementar con JWT real."""
    return {"telegram_id": 123456, "email": "user@example.com", "plan": "free"}


@router.get("/me")
async def get_me(current_user=Depends(get_current_user)):
    """Obtener información del usuario actual."""
    return current_user


@router.get("/usage")
async def get_usage(current_user=Depends(get_current_user)):
    """Obtener uso actual del usuario."""
    return {
        "ai_analyses_used": 1,
        "ai_analyses_limit": 2,
        "searches_used": 3,
        "searches_limit": 5,
        "remaining_analyses": 1,
        "remaining_searches": 2,
    }


@router.post("/sync")
async def sync_user_data(telegram_id: int, current_user=Depends(get_current_user)):
    """Sincroniza datos entre web y Telegram."""
    return {
        "telegram_id": telegram_id,
        "profile": {
            "experience_level": "junior",
            "technologies": "Python, JavaScript",
            "job_modality": "remote",
        },
        "usage": {"ai_analyses_used": 1, "ai_analyses_limit": 2},
    }

"""
Endpoint temporal para crear usuario web específico.
ELIMINAR DESPUÉS DE USAR.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

try:
    from job_bot.database import Database
    from werkzeug.security import generate_password_hash
except ImportError:
    from database import Database
    from werkzeug.security import generate_password_hash

router = APIRouter()

class CreateUserRequest(BaseModel):
    secret_key: str  # Para evitar que cualquiera cree usuarios
    telegram_id: int
    email: str
    password: str
    plan: str = "free"

@router.post("/tmp/create-user")
async def tmp_create_user(request: CreateUserRequest):
    """Endpoint temporal para crear usuario web."""
    
    # Verificar secret key (simple protection)
    if request.secret_key != "jobbot-setup-2024":
        raise HTTPException(status_code=403, detail="No autorizado")
    
    db = Database()
    
    # Verificar si ya existe
    existing = db.get_web_user(request.telegram_id)
    if existing:
        return {
            "status": "already_exists",
            "message": "El usuario ya existe",
            "email": existing.get("email"),
            "plan": existing.get("plan")
        }
    
    # Verificar si existe usuario Telegram
    telegram_user = db.get_user(request.telegram_id)
    if not telegram_user:
        db.create_user_if_not_exists(request.telegram_id, "Pisculichi")
    
    # Crear web_user
    password_hash = generate_password_hash(request.password)
    
    if db.db_type == "supabase":
        query = """
            INSERT INTO web_users 
            (telegram_id, email, password_hash, plan, job_tracker_enabled, is_admin)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
    else:
        query = """
            INSERT INTO web_users 
            (telegram_id, email, password_hash, plan, job_tracker_enabled, is_admin)
            VALUES (?, ?, ?, ?, ?, ?)
        """
    
    try:
        db._execute(query, (
            request.telegram_id,
            request.email,
            password_hash,
            request.plan,
            1 if request.plan in ['starter', 'pro', 'premium'] else 0,
            1  # is_admin
        ))
        
        return {
            "status": "created",
            "message": "Usuario creado exitosamente",
            "email": request.email,
            "telegram_id": request.telegram_id,
            "plan": request.plan,
            "login_url": "https://app-jobbot.vercel.app/login"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando usuario: {str(e)}")

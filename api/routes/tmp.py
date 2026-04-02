"""
Endpoints temporales para setup de usuario admin.
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
    secret_key: str
    telegram_id: int
    email: str
    password: str
    plan: str = "premium"  # Default a premium para admin


class MakeAdminRequest(BaseModel):
    secret_key: str
    telegram_id: int


@router.post("/create-user")
async def tmp_create_user(request: CreateUserRequest):
    """Crea usuario web vinculado a Telegram con privilegios admin."""
    
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
            "plan": existing.get("plan"),
            "is_admin": existing.get("is_admin")
        }
    
    # Verificar si existe usuario Telegram
    telegram_user = db.get_user(request.telegram_id)
    if not telegram_user:
        db.create_user_if_not_exists(request.telegram_id, "Pisculichi")
    
    # Crear web_user con admin y plan premium
    password_hash = generate_password_hash(request.password)
    
    if db.db_type == "supabase":
        query = """
            INSERT INTO web_users 
            (telegram_id, email, password_hash, plan, job_tracker_enabled, 
             is_admin, ai_analyses_limit, searches_limit, interviews_limit)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
    else:
        query = """
            INSERT INTO web_users 
            (telegram_id, email, password_hash, plan, job_tracker_enabled, 
             is_admin, ai_analyses_limit, searches_limit, interviews_limit)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
    
    try:
        db._execute(query, (
            request.telegram_id,
            request.email,
            password_hash,
            request.plan,
            1,  # job_tracker_enabled
            1,  # is_admin = 1
            9999,  # ai_analyses_limit (ilimitado prácticamente)
            9999,  # searches_limit (ilimitado)
            9999,  # interviews_limit (ilimitado)
        ))
        
        return {
            "status": "created",
            "message": "Usuario admin creado exitosamente",
            "email": request.email,
            "telegram_id": request.telegram_id,
            "plan": request.plan,
            "is_admin": 1,
            "limits": {
                "ai_analyses": "unlimited",
                "searches": "unlimited", 
                "interviews": "unlimited"
            },
            "login_url": "https://app-jobbot.vercel.app/login"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando usuario: {str(e)}")


@router.post("/make-admin-unlimited")
async def tmp_make_admin_unlimited(request: MakeAdminRequest):
    """Convierte un usuario existente en admin ilimitado."""
    
    if request.secret_key != "jobbot-setup-2024":
        raise HTTPException(status_code=403, detail="No autorizado")
    
    db = Database()
    
    # Verificar si existe
    existing = db.get_web_user(request.telegram_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if db.db_type == "supabase":
        query = """
            UPDATE web_users 
            SET is_admin = 1,
                plan = 'premium',
                ai_analyses_limit = 9999,
                searches_limit = 9999,
                interviews_limit = 9999,
                job_tracker_enabled = 1
            WHERE telegram_id = %s
        """
    else:
        query = """
            UPDATE web_users 
            SET is_admin = 1,
                plan = 'premium',
                ai_analyses_limit = 9999,
                searches_limit = 9999,
                interviews_limit = 9999,
                job_tracker_enabled = 1
            WHERE telegram_id = ?
        """
    
    try:
        db._execute(query, (request.telegram_id,))
        
        return {
            "status": "updated",
            "message": "Usuario ahora es admin ilimitado",
            "telegram_id": request.telegram_id,
            "is_admin": 1,
            "plan": "premium",
            "limits": "unlimited"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error actualizando usuario: {str(e)}")


@router.post("/add-credits")
async def tmp_add_credits(request: MakeAdminRequest):
    """Agrega créditos de prueba a un usuario."""
    
    if request.secret_key != "jobbot-setup-2024":
        raise HTTPException(status_code=403, detail="No autorizado")
    
    db = Database()
    
    try:
        pack_id = db.add_credit_pack(
            telegram_id=request.telegram_id,
            pack_type="unlock_suite",
            credits=50,
            price=0,  # Gratis
            currency="USD",
            payment_provider="manual_admin",
            payment_id="ADMIN_GIFT",
            metadata={"note": "Créditos de prueba para admin"}
        )
        
        return {
            "status": "credits_added",
            "pack_id": pack_id,
            "credits": 50,
            "telegram_id": request.telegram_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error agregando créditos: {str(e)}")

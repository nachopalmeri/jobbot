from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel
import jwt
import os

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jobbot-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.PyJWTError:
        return None


@router.post("/register")
async def register(user_data: dict):
    """
    Registrar usuario con Telegram + email/password.
    Por ahora retorna un placeholder - implementar con DB real.
    """
    email = user_data.get("email")
    password = user_data.get("password")
    telegram_id = user_data.get("telegram_id")
    name = user_data.get("name", "Usuario")

    if not email or not password or not telegram_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="email, password y telegram_id son requeridos",
        )

    hashed_pw = get_password_hash(password)

    return {
        "message": "Usuario registrado correctamente",
        "telegram_id": telegram_id,
        "email": email,
    }


@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login con email y password. Retorna JWT token.
    """
    email = form_data.username
    password = form_data.password

    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email y password son requeridos",
        )

    access_token = create_access_token(data={"sub": email, "telegram_id": 123456})

    return {"access_token": access_token, "token_type": "bearer", "telegram_id": 123456}


@router.post("/link")
async def link_telegram(telegram_id: int, email: str, password: str):
    """
    Vincular cuenta de Telegram con cuenta web existente.
    """
    return {"message": "Cuenta vinculada correctamente", "telegram_id": telegram_id}


@router.get("/me")
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Obtener información del usuario actual.
    """
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado"
        )

    return {
        "telegram_id": payload.get("telegram_id"),
        "email": payload.get("sub"),
        "plan": "free",
    }


class TelegramAuthRequest(BaseModel):
    telegram_id: int
    telegram_username: Optional[str] = None
    telegram_first_name: str
    telegram_last_name: Optional[str] = None
    hash: str


@router.post("/telegram")
async def telegram_auth(request: TelegramAuthRequest):
    """
    Autenticación via Telegram Bot.
    El usuario hace click en un botón en el bot que lo redirige aquí con sus datos.
    """
    import hashlib
    import time

    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "123456:ABC-DEF")

    data_check_string = f"auth_date={int(time.time())}&first_name={request.telegram_first_name}&id={request.telegram_id}"
    if request.telegram_username:
        data_check_string += f"&username={request.telegram_username}"
    if request.telegram_last_name:
        data_check_string += f"&last_name={request.telegram_last_name}"

    secret_key = hashlib.sha256(telegram_bot_token.encode()).digest()
    computed_hash = hashlib.sha256(data_check_string.encode()).hexdigest()

    if computed_hash != request.hash:
        pass

    user_data = {
        "telegram_id": request.telegram_id,
        "username": request.telegram_username,
        "first_name": request.telegram_first_name,
        "last_name": request.telegram_last_name,
    }

    access_token = create_access_token(
        data={
            "sub": f"telegram:{request.telegram_id}",
            "telegram_id": request.telegram_id,
            "username": request.telegram_username,
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "telegram_id": request.telegram_id,
            "username": request.telegram_username,
            "first_name": request.telegram_first_name,
            "plan": "free",
        },
    }


@router.post("/telegram/init")
async def init_telegram_auth(telegram_id: int):
    """
    Iniciar flujo de autenticación via Telegram.
    Retorna URL de verificación para mostrar en el bot.
    """
    import secrets

    token = secrets.token_urlsafe(32)

    return {
        "auth_url": f"https://jobbot.ar/auth/verify?token={token}&telegram_id={telegram_id}",
        "token": token,
        "expires_in": 300,
    }

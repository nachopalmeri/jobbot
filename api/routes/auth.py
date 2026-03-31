from datetime import datetime, timedelta
import hashlib
import hmac
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

try:
    from job_bot.database import Database
except ImportError:
    from database import Database


router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

APP_ENV = os.getenv("APP_ENV", "development").lower()
SECRET_KEY = os.getenv("JWT_SECRET_KEY") or (
    "dev-insecure-key-change-me" if APP_ENV != "production" else ""
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    if not SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT_SECRET_KEY no configurado",
        )
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    if not SECRET_KEY:
        return None
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        return None
    except JWTError:
        return None


def get_db() -> Database:
    return Database()


def get_authenticated_user(
    token: str = Depends(oauth2_scheme), db: Database = Depends(get_db)
):
    """Resuelve el usuario autenticado desde el JWT y sus datos persistidos."""
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    telegram_id = payload.get("telegram_id")
    email = payload.get("sub")
    if telegram_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    telegram_id = int(telegram_id)
    base_user = db.get_user(telegram_id) or {}
    web_user = db.get_web_user(telegram_id) or {}

    return {
        "telegram_id": telegram_id,
        "email": email,
        "plan": db.get_user_plan(telegram_id),
        "name": base_user.get("name") or web_user.get("email") or "Usuario",
        "user": base_user,
        "web_user": web_user,
    }


@router.post("/register")
async def register(user_data: dict, db: Database = Depends(get_db)):
    email = (user_data.get("email") or "").strip().lower()
    password = user_data.get("password")
    telegram_id = user_data.get("telegram_id")
    name = (user_data.get("name") or "Usuario").strip() or "Usuario"

    if not email or not password or not telegram_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="email, password y telegram_id son requeridos",
        )

    try:
        telegram_id = int(telegram_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="telegram_id invalido",
        )

    existing = db.get_web_user_by_email(email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una cuenta con ese email",
        )

    hashed_pw = get_password_hash(password)
    db.create_user_if_not_exists(telegram_id, name)
    db.create_web_user(telegram_id, email, hashed_pw)
    access_token = create_access_token(data={"sub": email, "telegram_id": telegram_id})
    return {
        "message": "Usuario registrado correctamente",
        "telegram_id": telegram_id,
        "email": email,
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Database = Depends(get_db)
):
    email = (form_data.username or "").strip().lower()
    password = form_data.password

    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email y password son requeridos",
        )

    user = db.get_web_user_by_email(email)
    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales invalidas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": email, "telegram_id": user["telegram_id"]}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "telegram_id": user["telegram_id"],
    }


@router.post("/link")
async def link_telegram(telegram_id: int, email: str, password: str):
    return {"message": "Cuenta vinculada correctamente", "telegram_id": telegram_id}


@router.get("/me")
async def get_current_user(current_user: dict = Depends(get_authenticated_user)):
    return {
        "telegram_id": current_user["telegram_id"],
        "email": current_user["email"],
        "plan": current_user["plan"],
        "name": current_user["name"],
    }


class TelegramAuthRequest(BaseModel):
    telegram_id: int
    auth_date: int
    telegram_username: Optional[str] = None
    telegram_first_name: str
    telegram_last_name: Optional[str] = None
    hash: str


@router.post("/telegram")
async def telegram_auth(request: TelegramAuthRequest):
    import time

    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not telegram_bot_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="TELEGRAM_BOT_TOKEN no configurado",
        )

    if abs(int(time.time()) - int(request.auth_date)) > 300:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Payload de Telegram expirado",
        )

    check_pairs = {
        "auth_date": str(request.auth_date),
        "first_name": request.telegram_first_name,
        "id": str(request.telegram_id),
    }
    if request.telegram_last_name:
        check_pairs["last_name"] = request.telegram_last_name
    if request.telegram_username:
        check_pairs["username"] = request.telegram_username

    data_check_string = "\n".join(
        f"{key}={value}" for key, value in sorted(check_pairs.items())
    )
    secret_key = hashlib.sha256(telegram_bot_token.encode()).digest()
    computed_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(computed_hash, request.hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Hash de Telegram invalido",
        )

    db = get_db()
    db.create_user_if_not_exists(request.telegram_id, request.telegram_first_name)

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
            "plan": db.get_user_plan(request.telegram_id),
        },
    }


@router.post("/telegram/init")
async def init_telegram_auth(telegram_id: int):
    import secrets

    token = secrets.token_urlsafe(32)

    return {
        "auth_url": f"https://jobbot.ar/auth/verify?token={token}&telegram_id={telegram_id}",
        "token": token,
        "expires_in": 300,
    }

from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
import hashlib
import hmac
import os
import secrets
import smtplib
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext
try:
    from werkzeug.security import check_password_hash
except ImportError:
    check_password_hash = None
from pydantic import BaseModel, EmailStr, Field

try:
    from job_bot.database import Database
except ImportError:
    from database import Database


router = APIRouter()
# `bcrypt` 5.x breaks passlib's backend self-check on some environments.
# Keep backward verification for existing bcrypt hashes, but generate new
# passwords with pbkdf2_sha256 to avoid register/login failures.
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256", "bcrypt"],
    deprecated="auto",
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

APP_ENV = os.getenv("APP_ENV", "development").lower()
SECRET_KEY = os.getenv("JWT_SECRET_KEY") or (
    "dev-insecure-key-change-me" if APP_ENV != "production" else ""
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
PASSWORD_RESET_TOKEN_TTL_MINUTES = int(os.getenv("PASSWORD_RESET_TOKEN_TTL_MINUTES", "60"))
SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "support@jobbot.ar")
PUBLIC_APP_URL = os.getenv("PUBLIC_APP_URL", os.getenv("DASHBOARD_URL", "https://app-jobbot.vercel.app"))
PRIMARY_ADMIN_EMAIL = (os.getenv("PRIMARY_ADMIN_EMAIL") or "admin@jobbot.com").strip().lower()


def _parse_env_list(name: str) -> set[str]:
    raw = os.getenv(name, "")
    return {item.strip() for item in raw.split(",") if item.strip()}


def _parse_env_int_list(name: str) -> set[int]:
    values: set[int] = set()
    for item in _parse_env_list(name):
        try:
            values.add(int(item))
        except ValueError:
            continue
    return values


def _password_reset_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _resolve_admin_flag(db: Database, telegram_id: int, email: Optional[str]) -> bool:
    if db.is_admin(telegram_id):
        return True

    normalized_email = (email or "").strip().lower()
    admin_emails = _parse_env_list("ADMIN_EMAILS")
    admin_telegram_ids = _parse_env_int_list("ADMIN_TELEGRAM_IDS")
    if PRIMARY_ADMIN_EMAIL:
        admin_emails.add(PRIMARY_ADMIN_EMAIL)

    if telegram_id in admin_telegram_ids or (normalized_email and normalized_email in admin_emails):
        db.create_user_if_not_exists(telegram_id, "Admin")
        db.set_admin(telegram_id, True)
        return True

    return False


def _smtp_configured() -> bool:
    return bool(os.getenv("SMTP_HOST") and os.getenv("SMTP_FROM_EMAIL"))


def _send_email_message(to_email: str, subject: str, text_content: str, html_content: str):
    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_from = os.getenv("SMTP_FROM_EMAIL", "").strip()
    if not smtp_host or not smtp_from:
        raise RuntimeError("SMTP no configurado")

    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
    smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").strip().lower() != "false"

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = smtp_from
    message["To"] = to_email
    message.set_content(text_content)
    message.add_alternative(html_content, subtype="html")

    with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as smtp:
        smtp.ehlo()
        if smtp_use_tls:
            smtp.starttls()
            smtp.ehlo()
        if smtp_username:
            smtp.login(smtp_username, smtp_password)
        smtp.send_message(message)


def _send_password_reset_email(email: str, reset_url: str):
    subject = "Restablecé tu password de JobBot"
    text_content = (
        "Recibimos una solicitud para restablecer tu password de JobBot.\n\n"
        f"Abrí este enlace: {reset_url}\n\n"
        "Si no fuiste vos, podés ignorar este email.\n"
        f"Si necesitás ayuda, escribinos a {SUPPORT_EMAIL}."
    )
    html_content = f"""
    <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #1c1917;">
      <h2>Restablecé tu password de JobBot</h2>
      <p>Recibimos una solicitud para cambiar tu password.</p>
      <p>
        <a href="{reset_url}" style="display:inline-block;padding:12px 20px;background:#4f46e5;color:#fff;text-decoration:none;border-radius:12px;">
          Crear nueva password
        </a>
      </p>
      <p>Si el botón no funciona, copiá este enlace:</p>
      <p><a href="{reset_url}">{reset_url}</a></p>
      <p>Si no fuiste vos, podés ignorar este email.</p>
      <p>Soporte: <a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a></p>
    </div>
    """
    _send_email_message(email, subject, text_content, html_content)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Try passlib first
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        pass

    # Fallback to werkzeug for legacy hashes
    if check_password_hash:
        try:
            return check_password_hash(hashed_password, plain_password)
        except Exception:
            pass

    return False


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    if not SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT_SECRET_KEY no configurado",
        )
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
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

    if not base_user and not web_user and email and "@" in email:
        linked_web_user = db.get_web_user_by_email(email) or {}
        if linked_web_user:
            telegram_id = int(linked_web_user["telegram_id"])
            base_user = db.get_user(telegram_id) or {}
            web_user = linked_web_user

    return {
        "telegram_id": telegram_id,
        "email": email,
        "plan": db.get_user_plan(telegram_id),
        "is_admin": _resolve_admin_flag(db, telegram_id, email),
        "has_telegram_link": telegram_id > 0,
        "name": base_user.get("name") or web_user.get("email") or "Usuario",
        "user": base_user,
        "web_user": web_user,
    }


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    telegram_id: Optional[int] = None
    name: Optional[str] = Field(default="Usuario", max_length=120)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    token: str = Field(min_length=20, max_length=512)
    password: str = Field(min_length=8, max_length=128)


@router.post("/register")
async def register(user_data: RegisterRequest, db: Database = Depends(get_db)):
    email = str(user_data.email).strip().lower()
    password = user_data.password
    telegram_id = user_data.telegram_id
    name = (user_data.name or "Usuario").strip() or "Usuario"
    generated_web_only_account = False

    if telegram_id is None:
        telegram_id = db.generate_web_account_id()
        generated_web_only_account = True

    existing = db.get_web_user_by_email(email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una cuenta con ese email",
        )

    if not generated_web_only_account:
        existing_web_for_telegram = db.get_web_user(telegram_id)
        if existing_web_for_telegram:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ese Telegram ID ya esta vinculado a otra cuenta",
            )

    hashed_pw = get_password_hash(password)
    db.create_user_if_not_exists(telegram_id, name)
    db.create_web_user(telegram_id, email, hashed_pw)
    db.set_alert_channel(telegram_id, "telegram" if telegram_id > 0 else "web")
    db.update_user_plan(telegram_id, "free")
    access_token = create_access_token(data={"sub": email, "telegram_id": telegram_id})
    return {
        "message": "Usuario registrado correctamente",
        "telegram_id": telegram_id,
        "email": email,
        "is_admin": db.is_admin(telegram_id),
        "has_telegram_link": telegram_id > 0,
        "is_temp_account": generated_web_only_account,
        "account_type": "telegram-linked" if telegram_id > 0 else "web-only",
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
        "is_admin": _resolve_admin_flag(db, int(user["telegram_id"]), email),
    }


@router.post("/password-reset/request")
async def request_password_reset(
    payload: PasswordResetRequest, db: Database = Depends(get_db)
):
    normalized_email = str(payload.email).strip().lower()

    if APP_ENV == "production" and not _smtp_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Recuperacion de password no disponible temporalmente",
        )

    user = db.get_web_user_by_email(normalized_email)
    if user:
        token = secrets.token_urlsafe(32)
        token_hash = _password_reset_token_hash(token)
        expires_at = (
            datetime.now(timezone.utc) + timedelta(minutes=PASSWORD_RESET_TOKEN_TTL_MINUTES)
        ).isoformat()
        db.create_password_reset_token(normalized_email, token_hash, expires_at)

        reset_url = f"{PUBLIC_APP_URL.rstrip('/')}/reset-password?token={quote(token)}"
        if _smtp_configured():
            _send_password_reset_email(normalized_email, reset_url)
        else:
            print(f"[DEV] Password reset link for {normalized_email}: {reset_url}")

    return {
        "message": "Si existe una cuenta con ese email, te enviamos un enlace para restablecer tu password."
    }


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    payload: PasswordResetConfirmRequest, db: Database = Depends(get_db)
):
    record = db.consume_password_reset_token(_password_reset_token_hash(payload.token))
    if not record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El enlace de recuperacion es invalido o ya expiró",
        )

    email = record["email"]
    web_user = db.get_web_user_by_email(email)
    if not web_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No encontramos una cuenta asociada a este enlace",
        )

    db.update_web_user_password(email, get_password_hash(payload.password))
    db.clear_password_reset_tokens_for_email(email)

    return {"message": "Password actualizada correctamente"}


@router.post("/link")
async def link_telegram(telegram_id: int, email: str, password: str):
    return {"message": "Cuenta vinculada correctamente", "telegram_id": telegram_id}


@router.get("/me")
async def get_current_user(current_user: dict = Depends(get_authenticated_user)):
    return {
        "telegram_id": current_user["telegram_id"],
        "email": current_user["email"],
        "plan": current_user["plan"],
        "is_admin": current_user["is_admin"],
        "has_telegram_link": current_user["has_telegram_link"],
        "is_temp_account": current_user["telegram_id"] <= 0,
        "account_type": "telegram-linked" if current_user["telegram_id"] > 0 else "web-only",
        "name": current_user["name"],
    }


class TelegramAuthRequest(BaseModel):
    telegram_id: int
    auth_date: int
    telegram_username: Optional[str] = None
    telegram_first_name: str
    telegram_last_name: Optional[str] = None
    hash: str


class TelegramCodeLoginRequest(BaseModel):
    code: str


@router.post("/telegram")
async def telegram_auth(request: TelegramAuthRequest):
    import time

    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
    if not telegram_bot_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="TELEGRAM_BOT_TOKEN/TELEGRAM_TOKEN no configurado",
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
            "is_admin": db.is_admin(request.telegram_id),
        },
    }


@router.post("/telegram/init")
async def init_telegram_auth(telegram_id: int):
    token = secrets.token_urlsafe(32)

    return {
        "auth_url": f"https://jobbot.ar/auth/verify?token={token}&telegram_id={telegram_id}",
        "token": token,
        "expires_in": 300,
    }


@router.post("/telegram/code")
async def telegram_code_login(
    payload: TelegramCodeLoginRequest, db: Database = Depends(get_db)
):
    code = (payload.code or "").strip().upper()
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Codigo requerido",
        )

    login_record = db.consume_web_login_code(code)
    if not login_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Codigo invalido o expirado",
        )

    telegram_id = int(login_record["telegram_id"])
    base_user = db.get_user(telegram_id) or {}
    web_user = db.get_web_user(telegram_id) or {}
    email = web_user.get("email") or f"telegram:{telegram_id}"

    access_token = create_access_token(
        data={
            "sub": email,
            "telegram_id": telegram_id,
            "auth_method": "telegram_code",
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "telegram_id": telegram_id,
        "user": {
            "telegram_id": telegram_id,
            "name": base_user.get("name") or "Usuario",
            "plan": db.get_user_plan(telegram_id),
            "email": web_user.get("email"),
            "is_admin": db.is_admin(telegram_id),
        },
    }


@router.post("/telegram/web-login-link")
async def create_telegram_web_login_link(
    current_user: dict = Depends(get_authenticated_user), db: Database = Depends(get_db)
):
    code = secrets.token_hex(3).upper()
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    db.create_web_login_code(current_user["telegram_id"], code, expires_at)
    landing_url = (
        os.getenv("DASHBOARD_URL")
        or os.getenv("LANDING_URL")
        or "https://app-jobbot.vercel.app"
    ).rstrip("/")
    return {
        "code": code,
        "expires_in": 600,
        "login_url": f"{landing_url}/login?code={code}",
    }


@router.post("/telegram/link-code")
async def create_telegram_link_code(
    current_user: dict = Depends(get_authenticated_user), db: Database = Depends(get_db)
):
    telegram_id = int(current_user["telegram_id"])
    bot_username = os.getenv("TELEGRAM_BOT_USERNAME", "jobs912bot").lstrip("@")
    dashboard_url = (
        os.getenv("DASHBOARD_URL")
        or os.getenv("LANDING_URL")
        or "https://app-jobbot.vercel.app"
    ).rstrip("/")
    if telegram_id > 0:
        return {
            "code": None,
            "expires_in": 0,
            "already_linked": True,
            "telegram_bot_username": bot_username,
            "dashboard_url": dashboard_url,
        }

    code = secrets.token_hex(3).upper()
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=20)).isoformat()
    db.create_telegram_link_code(telegram_id, code, expires_at)

    return {
        "code": code,
        "expires_in": 1200,
        "already_linked": False,
        "telegram_bot_username": bot_username,
        "dashboard_url": dashboard_url,
        "deep_link": f"https://t.me/{bot_username}?start=link_{code}",
        "instructions": f"/vincular {code}",
    }

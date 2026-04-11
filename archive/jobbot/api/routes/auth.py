from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import os
import secrets
from typing import Optional

from fastapi import APIRouter, Body, Depends, Form, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Import security utilities
try:
    from ..core.security import (
        create_access_token as security_create_access_token,
        create_refresh_token as security_create_refresh_token,
        decode_token as security_decode_token,
        validate_jwt_secret,
        hash_token,
        TokenBlacklist,
        RefreshTokenManager,
        get_token_blacklist,
        get_refresh_token_manager,
    )
    from ..core import security as security_module
except ImportError:
    from api.core.security import (
        create_access_token as security_create_access_token,
        create_refresh_token as security_create_refresh_token,
        decode_token as security_decode_token,
        validate_jwt_secret,
        hash_token,
        TokenBlacklist,
        RefreshTokenManager,
        get_token_blacklist,
        get_refresh_token_manager,
    )
    from api.core import security as security_module

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

# JWT Configuration
APP_ENV = os.getenv("APP_ENV", "development")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
REFRESH_TOKEN_EXPIRE_DAYS = 7


def _landing_url() -> str:
    configured = os.getenv("LANDING_URL")
    if configured:
        return configured.rstrip("/")
    app_env = os.getenv("APP_ENV", "development").lower()
    return "https://jobbot.ar" if app_env == "production" else "http://127.0.0.1:3000"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a new access token using the security module."""
    return security_create_access_token(data, expires_delta)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token using the security module."""
    return security_decode_token(token)


def verify_telegram_auth_payload(
    telegram_id: int,
    auth_date: int,
    hash_value: str,
    first_name: str,
    last_name: Optional[str] = None,
    username: Optional[str] = None,
) -> bool:
    """Verify Telegram authentication payload."""
    return security_module.verify_telegram_auth(
        telegram_id=telegram_id,
        auth_date=auth_date,
        hash_value=hash_value,
        first_name=first_name,
        last_name=last_name,
        username=username,
    )


def get_db() -> Database:
    return Database()


def get_token_blacklist_instance(db: Database = Depends(get_db)) -> TokenBlacklist:
    """Dependency to get the token blacklist instance."""
    return get_token_blacklist(db)


def get_refresh_manager_instance(db: Database = Depends(get_db)) -> RefreshTokenManager:
    """Dependency to get the refresh token manager instance."""
    return get_refresh_token_manager(db)


def _auth_identity_snapshot(db: Database, telegram_id: int, email: Optional[str]) -> dict:
    base_user = db.get_user(telegram_id) or {}
    web_user = db.get_web_user(telegram_id) or {}
    has_telegram_link = telegram_id > 0
    return {
        "telegram_id": telegram_id,
        "email": email,
        "name": base_user.get("name") or web_user.get("email") or "Usuario",
        "plan": db.get_user_plan(telegram_id),
        "has_telegram_link": has_telegram_link,
        "account_type": "telegram-linked" if has_telegram_link else "web-only",
        "user": base_user,
        "web_user": web_user,
    }


def get_authenticated_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Database = Depends(get_db),
    blacklist: TokenBlacklist = Depends(get_token_blacklist_instance),
):
    """
    Resuelve el usuario autenticado desde el JWT y sus datos persistidos.
    
    Args:
        token: JWT token from Authorization header
        db: Database instance
        blacklist: Token blacklist instance for checking revoked tokens
    
    Returns:
        User dictionary with authentication details
    
    Raises:
        HTTPException: If token is invalid, expired, or revoked
    """
    # Check if token is blacklisted
    # NOTE: TokenBlacklist hashes internally; passing a pre-hashed value
    # would hash twice and bypass revocation checks.
    if blacklist.is_token_revoked(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token ha sido revocado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Decode and validate token
    payload = security_decode_token(token)
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
    if request is not None:
        request.state.user_id = telegram_id

    # Si el token viejo apunta a una cuenta web temporal ya migrada,
    # resolvemos la identidad final por email para no romper la sesión.
    if not db.get_user(telegram_id) and not db.get_web_user(telegram_id) and email and "@" in email:
        linked_web_user = db.get_web_user_by_email(email) or {}
        if linked_web_user:
            telegram_id = int(linked_web_user["telegram_id"])

    snapshot = _auth_identity_snapshot(db, telegram_id, email)
    snapshot.update({
        "token": token,
        "token_hash": hash_token(token),
    })
    return snapshot


@router.post("/register")
async def register(
    user_data: dict,
    db: Database = Depends(get_db),
    refresh_manager: RefreshTokenManager = Depends(get_refresh_manager_instance),
):
    """
    Register a new user with enhanced security.
    
    Args:
        user_data: User registration data
        db: Database instance
        refresh_manager: Refresh token manager for token rotation
    
    Returns:
        User data with access and refresh tokens
    """
    email = (user_data.get("email") or "").strip().lower()
    password = user_data.get("password")
    telegram_id = user_data.get("telegram_id")
    name = (user_data.get("name") or "Usuario").strip() or "Usuario"
    device_info = user_data.get("device_info")

    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="email y password son requeridos",
        )

    telegram_linked = bool(str(telegram_id).strip()) if telegram_id is not None else False
    if telegram_linked:
        try:
            telegram_id = int(telegram_id)
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="telegram_id invalido",
            )
    else:
        telegram_id = db.generate_web_account_id()

    existing = db.get_web_user_by_email(email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una cuenta con ese email",
        )

    if telegram_linked:
        existing_web_for_telegram = db.get_web_user(telegram_id)
        if existing_web_for_telegram:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ese Telegram ID ya esta vinculado a otra cuenta",
            )

        if db.get_user(telegram_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Ese Telegram ID ya existe en JobBot. Para vincular una cuenta activa "
                    "necesitas verificarla desde Telegram."
                ),
            )

    hashed_pw = get_password_hash(password)
    db.create_user_if_not_exists(telegram_id, name)
    db.create_web_user(telegram_id, email, hashed_pw)
    db.set_alert_channel(telegram_id, "telegram" if telegram_linked else "web")
    
    # Create token pair with rotation
    access_token, refresh_token = refresh_manager.create_refresh_token_pair(
        user_id=telegram_id,
        email=email,
        device_info=device_info,
    )
    
    return {
        "message": "Usuario registrado correctamente",
        "telegram_id": telegram_id,
        "email": email,
        "name": name,
        "plan": db.get_user_plan(telegram_id),
        "has_telegram_link": telegram_linked,
        "account_type": "telegram-linked" if telegram_linked else "web-only",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/token")
async def login(
    username: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    db: Database = Depends(get_db),
    refresh_manager: RefreshTokenManager = Depends(get_refresh_manager_instance),
):
    """
    Login endpoint with enhanced security and refresh token rotation.
    
    Args:
        form_data: OAuth2 form with username (email) and password
        db: Database instance
        refresh_manager: Refresh token manager for token rotation
    
    Returns:
        Access and refresh tokens
    """
    email = (username or "").strip().lower()

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

    # Create token pair with rotation
    access_token, refresh_token = refresh_manager.create_refresh_token_pair(
        user_id=user["telegram_id"],
        email=email,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "telegram_id": user["telegram_id"],
        "email": email,
        "name": user.get("name") or (db.get_user(int(user["telegram_id"])) or {}).get("name") or "Usuario",
        "plan": db.get_user_plan(int(user["telegram_id"])),
        "has_telegram_link": int(user["telegram_id"]) > 0,
        "account_type": "telegram-linked" if int(user["telegram_id"]) > 0 else "web-only",
    }


@router.post("/refresh")
async def refresh_token(
    refresh_token: Optional[str] = Body(None, embed=True),
    db: Database = Depends(get_db),
    refresh_manager: RefreshTokenManager = Depends(get_refresh_manager_instance),
):
    """
    Refresh access token using a valid refresh token.
    Implements refresh token rotation for enhanced security.
    
    Args:
        refresh_token: Valid refresh token
        db: Database instance
        refresh_manager: Refresh token manager
    
    Returns:
        New access and refresh tokens
    """
    # Validate the refresh token
    refresh_token = (refresh_token or "").strip()
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="refresh_token es requerido",
        )

    payload = security_decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresh invalido",
        )
    
    telegram_id = payload.get("telegram_id")
    email = payload.get("sub")
    
    if not telegram_id or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido",
        )
    
    # Rotate the refresh token
    result = refresh_manager.rotate_refresh_token(
        old_refresh_token=refresh_token,
        email=email,
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresh invalido o revocado",
        )
    
    new_access_token, new_refresh_token = result
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "telegram_id": telegram_id,
    }


@router.post("/logout")
async def logout(
    current_user: dict = Depends(get_authenticated_user),
    blacklist: TokenBlacklist = Depends(get_token_blacklist_instance),
    refresh_manager: RefreshTokenManager = Depends(get_refresh_manager_instance),
):
    """
    Logout endpoint that revokes the current access token and refresh tokens.
    
    Args:
        current_user: Currently authenticated user
        blacklist: Token blacklist instance
        refresh_manager: Refresh token manager
    
    Returns:
        Success message
    """
    # Blacklist the current access token
    token = current_user.get("token")
    token_hash = current_user.get("token_hash")
    
    if token and token_hash:
        # Decode to get expiration time
        payload = security_decode_token(token)
        if payload:
            exp = payload.get("exp")
            if exp:
                blacklist.revoke_token(token, datetime.fromtimestamp(exp, tz=timezone.utc))
    
    # Revoke all refresh tokens for this user (logout from all devices)
    refresh_manager.revoke_all_user_tokens(current_user["telegram_id"])
    
    return {
        "message": "Sesion cerrada correctamente",
        "telegram_id": current_user["telegram_id"],
    }


@router.post("/logout-all")
async def logout_all_devices(
    current_user: dict = Depends(get_authenticated_user),
    blacklist: TokenBlacklist = Depends(get_token_blacklist_instance),
    refresh_manager: RefreshTokenManager = Depends(get_refresh_manager_instance),
):
    """
    Logout from all devices by revoking all tokens.
    
    Args:
        current_user: Currently authenticated user
        blacklist: Token blacklist instance
        refresh_manager: Refresh token manager
    
    Returns:
        Success message
    """
    # Blacklist the current access token
    token = current_user.get("token")
    token_hash = current_user.get("token_hash")
    
    if token and token_hash:
        payload = security_decode_token(token)
        if payload:
            exp = payload.get("exp")
            if exp:
                blacklist.revoke_token(token, datetime.fromtimestamp(exp, tz=timezone.utc))
    
    # Revoke all refresh tokens for this user
    refresh_manager.revoke_all_user_tokens(current_user["telegram_id"])
    
    return {
        "message": "Sesion cerrada en todos los dispositivos",
        "telegram_id": current_user["telegram_id"],
    }


@router.get("/me")
async def get_current_user(current_user: dict = Depends(get_authenticated_user)):
    return {
        "telegram_id": current_user["telegram_id"],
        "email": current_user["email"],
        "plan": current_user["plan"],
        "name": current_user["name"],
        "has_telegram_link": current_user["telegram_id"] > 0,
        "account_type": "telegram-linked" if current_user["telegram_id"] > 0 else "web-only",
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


class TelegramLinkRequest(BaseModel):
    email: str
    password: str


def _create_telegram_link_code_payload(current_user: dict, db: Database) -> dict:
    telegram_id = int(current_user["telegram_id"])
    if telegram_id > 0:
        return {
            "already_linked": True,
            "has_telegram_link": True,
            "telegram_id": telegram_id,
            "plan": db.get_user_plan(telegram_id),
            "account_type": "telegram-linked",
        }

    code = secrets.token_hex(3).upper()
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    db.create_telegram_link_code(telegram_id, code, expires_at)

    landing_url = _landing_url()
    bot_username = (os.getenv("TELEGRAM_BOT_USERNAME") or "jobs912bot").lstrip("@")
    deep_link = f"https://t.me/{bot_username}?start=link_{code}"

    return {
        "code": code,
        "expires_in": 600,
        "telegram_bot_username": bot_username,
        "deep_link": deep_link,
        "landing_url": landing_url,
        "instructions": f"/vincular {code}",
        "plan": db.get_user_plan(telegram_id),
        "has_telegram_link": False,
        "account_type": "web-only",
    }


@router.post("/link")
async def link_telegram(
    payload: TelegramLinkRequest,
    current_user: dict = Depends(get_authenticated_user),
    db: Database = Depends(get_db),
):
    current_telegram_id = int(current_user["telegram_id"])
    if current_telegram_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debes iniciar sesión con Telegram para vincular una cuenta web",
        )

    email = (payload.email or "").strip().lower()
    if not email or not payload.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="email y password son requeridos",
        )

    web_user = db.get_web_user_by_email(email)
    if not web_user or not verify_password(payload.password, web_user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales invalidas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    source_telegram_id = int(web_user["telegram_id"])
    if source_telegram_id == current_telegram_id:
        return {
            "message": "La cuenta ya estaba vinculada",
            "telegram_id": current_telegram_id,
            "email": email,
            "has_telegram_link": True,
            "account_type": "telegram-linked",
        }

    if source_telegram_id > 0 and source_telegram_id != current_telegram_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esa cuenta ya está vinculada a otro Telegram",
        )

    db.link_web_account_to_telegram(
        source_telegram_id,
        current_telegram_id,
        current_user.get("name") or "Usuario",
    )

    return {
        "message": "Cuenta vinculada correctamente",
        "telegram_id": current_telegram_id,
        "email": email,
        "has_telegram_link": True,
        "account_type": "telegram-linked",
    }


@router.post("/telegram")
async def telegram_auth(
    request: TelegramAuthRequest,
    db: Database = Depends(get_db),
    refresh_manager: RefreshTokenManager = Depends(get_refresh_manager_instance),
):
    """
    Authenticate via Telegram WebApp with enhanced security.
    
    Args:
        request: Telegram authentication data
        refresh_manager: Refresh token manager
    
    Returns:
        Access and refresh tokens
    """
    # Verify Telegram auth
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not telegram_bot_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="TELEGRAM_BOT_TOKEN no configurado",
        )

    # Verify the Telegram auth payload
    is_valid = verify_telegram_auth_payload(
        telegram_id=request.telegram_id,
        auth_date=request.auth_date,
        hash_value=request.hash,
        first_name=request.telegram_first_name,
        last_name=request.telegram_last_name,
        username=request.telegram_username,
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticacion de Telegram invalida",
        )

    db.create_user_if_not_exists(request.telegram_id, request.telegram_first_name)

    # Create token pair with rotation
    access_token, refresh_token = refresh_manager.create_refresh_token_pair(
        user_id=request.telegram_id,
        email=f"telegram:{request.telegram_id}",
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
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
    token = secrets.token_urlsafe(32)

    return {
        "auth_url": f"{_landing_url()}/auth/verify?token={token}&telegram_id={telegram_id}",
        "token": token,
        "expires_in": 300,
    }


@router.post("/telegram/code")
async def telegram_code_login(
    payload: TelegramCodeLoginRequest,
    db: Database = Depends(get_db),
    refresh_manager: RefreshTokenManager = Depends(get_refresh_manager_instance),
):
    """
    Login with Telegram code using refresh token rotation.
    
    Args:
        payload: Login code data
        db: Database instance
        refresh_manager: Refresh token manager
    
    Returns:
        Access and refresh tokens
    """
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

    # Create token pair with rotation
    access_token, refresh_token = refresh_manager.create_refresh_token_pair(
        user_id=telegram_id,
        email=email,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "telegram_id": telegram_id,
        "email": email,
        "user": {
            "telegram_id": telegram_id,
            "name": base_user.get("name") or "Usuario",
            "plan": db.get_user_plan(telegram_id),
            "email": web_user.get("email"),
        },
        "plan": db.get_user_plan(telegram_id),
        "has_telegram_link": telegram_id > 0,
        "account_type": "telegram-linked" if telegram_id > 0 else "web-only",
    }


@router.post("/telegram/web-login-link")
async def create_telegram_web_login_link(
    current_user: dict = Depends(get_authenticated_user),
    db: Database = Depends(get_db),
):
    code = secrets.token_hex(3).upper()
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    db.create_web_login_code(current_user["telegram_id"], code, expires_at)
    landing_url = _landing_url()
    return {
        "code": code,
        "expires_in": 600,
        "login_url": f"{landing_url}/login?code={code}",
    }


@router.post("/telegram/link-code")
async def create_telegram_link_code(
    current_user: dict = Depends(get_authenticated_user),
    db: Database = Depends(get_db),
):
    return _create_telegram_link_code_payload(current_user, db)

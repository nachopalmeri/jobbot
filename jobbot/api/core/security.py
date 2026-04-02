"""
Core security utilities for JobBot API.
Includes JWT validation, token blacklist, and refresh token rotation.
"""

import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from jose import ExpiredSignatureError, JWTError, jwt


# JWT Configuration - NO FALLBACK SECRETS in production
APP_ENV = os.getenv("APP_ENV", "development").lower()
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
REFRESH_TOKEN_EXPIRE_DAYS = 7


def validate_jwt_secret() -> str:
    """
    Validate and return JWT secret key.
    Raises HTTPException if not configured in production.
    """
    if not JWT_SECRET_KEY:
        if APP_ENV == "production":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="JWT_SECRET_KEY not configured",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT_SECRET_KEY not configured",
        )
    
    # Check for weak/insecure secrets
    weak_secrets = [
        "dev-insecure-key-change-me",
        "secret",
        "test",
        "123456",
        "password",
        "jwt-secret",
    ]
    
    if JWT_SECRET_KEY.lower() in weak_secrets or len(JWT_SECRET_KEY) < 32:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT_SECRET_KEY is too weak. Minimum 32 characters required.",
        )
    
    return JWT_SECRET_KEY


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
    secret_key: Optional[str] = None
) -> str:
    """
    Create a new access token.
    
    Args:
        data: Dictionary of claims to encode
        expires_delta: Optional custom expiration time
        secret_key: Optional override for JWT secret
    
    Returns:
        Encoded JWT string
    """
    secret = secret_key or validate_jwt_secret()
    
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    )
    to_encode.update({"exp": expire, "type": "access"})
    
    return jwt.encode(to_encode, secret, algorithm=ALGORITHM)


def create_refresh_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
    secret_key: Optional[str] = None
) -> str:
    """
    Create a new refresh token.
    
    Args:
        data: Dictionary of claims to encode
        expires_delta: Optional custom expiration time
        secret_key: Optional override for JWT secret
    
    Returns:
        Encoded JWT string
    """
    secret = secret_key or validate_jwt_secret()
    
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    to_encode.update({"exp": expire, "type": "refresh"})
    
    return jwt.encode(to_encode, secret, algorithm=ALGORITHM)


def decode_token(
    token: str,
    secret_key: Optional[str] = None
) -> Optional[dict]:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT string to decode
        secret_key: Optional override for JWT secret
    
    Returns:
        Decoded token payload or None if invalid
    """
    try:
        secret = secret_key or validate_jwt_secret()
        return jwt.decode(token, secret, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        return None
    except JWTError:
        return None


def verify_telegram_auth(
    telegram_id: int,
    auth_date: int,
    hash_value: str,
    first_name: str,
    last_name: Optional[str] = None,
    username: Optional[str] = None,
    bot_token: Optional[str] = None
) -> bool:
    """
    Verify Telegram WebApp authentication.
    
    Args:
        telegram_id: Telegram user ID
        auth_date: Unix timestamp from Telegram
        hash_value: Hash from Telegram
        first_name: User's first name
        last_name: Optional last name
        username: Optional username
        bot_token: Telegram bot token (from env if not provided)
    
    Returns:
        True if authentication is valid
    """
    import time
    
    token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return False
    
    # Check if payload is too old (5 minutes)
    if abs(int(time.time()) - int(auth_date)) > 300:
        return False
    
    # Build data check string
    check_pairs = {
        "auth_date": str(auth_date),
        "first_name": first_name,
        "id": str(telegram_id),
    }
    
    if last_name:
        check_pairs["last_name"] = last_name
    if username:
        check_pairs["username"] = username
    
    data_check_string = "\n".join(
        f"{key}={value}" for key, value in sorted(check_pairs.items())
    )
    
    # Compute hash
    secret_key = hashlib.sha256(token.encode()).digest()
    computed_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()
    
    return hmac.compare_digest(computed_hash, hash_value)


def generate_token_id() -> str:
    """Generate a unique token identifier."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Create a hash of a token for blacklist storage."""
    return hashlib.sha256(token.encode()).hexdigest()


class TokenBlacklist:
    """
    Token blacklist manager for handling revoked tokens.
    Uses database for persistence.
    """
    
    def __init__(self, database=None):
        self.database = database
    
    def revoke_token(self, token: str, expires_at: Optional[datetime] = None) -> bool:
        """
        Add a token to the blacklist.
        
        Args:
            token: JWT token to revoke
            expires_at: When the token expires (for cleanup)
        
        Returns:
            True if successfully added to blacklist
        """
        if self.database is None:
            return False
        
        try:
            token_hash = hash_token(token)
            exp = expires_at or (datetime.now(timezone.utc) + timedelta(hours=24))
            
            self.database.add_to_token_blacklist(
                token_hash=token_hash,
                expires_at=int(exp.timestamp())
            )
            return True
        except Exception:
            return False
    
    def is_token_revoked(self, token: str) -> bool:
        """
        Check if a token has been revoked.
        
        Args:
            token: JWT token to check
        
        Returns:
            True if token is revoked
        """
        if self.database is None:
            return False
        
        try:
            token_hash = hash_token(token)
            return self.database.is_token_blacklisted(token_hash)
        except Exception:
            return False
    
    def cleanup_expired_tokens(self) -> int:
        """
        Remove expired tokens from the blacklist.
        
        Returns:
            Number of tokens removed
        """
        if self.database is None:
            return 0
        
        try:
            return self.database.cleanup_token_blacklist()
        except Exception:
            return 0


class RefreshTokenManager:
    """
    Manager for refresh token rotation.
    Implements refresh token rotation for enhanced security.
    """
    
    def __init__(self, database=None):
        self.database = database
    
    def create_refresh_token_pair(
        self,
        user_id: int,
        email: str,
        device_info: Optional[str] = None
    ) -> tuple[str, str]:
        """
        Create a new refresh token with rotation support.
        
        Args:
            user_id: User ID
            email: User email
            device_info: Optional device/client info
        
        Returns:
            Tuple of (access_token, refresh_token)
        """
        # Generate token family ID for rotation tracking
        family_id = generate_token_id()
        
        # Create access token
        access_token = create_access_token(
            data={
                "sub": email,
                "telegram_id": user_id,
                "token_family": family_id,
            }
        )
        
        # Create refresh token
        refresh_token = create_refresh_token(
            data={
                "sub": email,
                "telegram_id": user_id,
                "token_family": family_id,
                "token_id": generate_token_id(),
            }
        )
        
        # Store refresh token hash in database
        if self.database:
            try:
                self.database.store_refresh_token(
                    user_id=user_id,
                    token_hash=hash_token(refresh_token),
                    family_id=family_id,
                    device_info=device_info,
                    expires_at=int((datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)).timestamp())
                )
            except Exception:
                pass
        
        return access_token, refresh_token
    
    def rotate_refresh_token(
        self,
        old_refresh_token: str,
        email: str,
        device_info: Optional[str] = None
    ) -> Optional[tuple[str, str]]:
        """
        Rotate a refresh token (one-time use).
        
        Args:
            old_refresh_token: Current refresh token
            email: User email
            device_info: Optional device/client info
        
        Returns:
            Tuple of (new_access_token, new_refresh_token) or None if invalid
        """
        # Decode old token
        payload = decode_token(old_refresh_token)
        if not payload:
            return None
        
        # Verify it's a refresh token
        if payload.get("type") != "refresh":
            return None
        
        user_id = payload.get("telegram_id")
        family_id = payload.get("token_family")
        token_id = payload.get("token_id")
        
        if not all([user_id, family_id]):
            return None
        
        # Check if token is valid in database (not revoked)
        if self.database:
            try:
                old_hash = hash_token(old_refresh_token)
                if not self.database.is_refresh_token_valid(old_hash, family_id):
                    # Token was already used - possible reuse attack
                    # Revoke entire token family
                    self.database.revoke_token_family(family_id)
                    return None
                
                # Mark old token as used
                self.database.revoke_refresh_token(old_hash)
            except Exception:
                return None
        
        # Create new token pair
        return self.create_refresh_token_pair(
            user_id=user_id,
            email=email,
            device_info=device_info
        )
    
    def revoke_all_user_tokens(self, user_id: int) -> bool:
        """
        Revoke all refresh tokens for a user (logout all devices).
        
        Args:
            user_id: User ID
        
        Returns:
            True if successful
        """
        if self.database is None:
            return False
        
        try:
            self.database.revoke_all_user_refresh_tokens(user_id)
            return True
        except Exception:
            return False


# Factory functions
def get_token_blacklist(database=None):
    """Create a TokenBlacklist instance."""
    return TokenBlacklist(database)


def get_refresh_token_manager(database=None):
    """Create a RefreshTokenManager instance."""
    return RefreshTokenManager(database)

# Critical Security Fixes - Implementation Guide

> Step-by-step implementation for the 3 critical security issues identified in the audit.

---

## 🔴 Fix 1: Remove Hardcoded Admin Credentials

### Current Problem
```typescript
// dashboard/src/app/api/backend/[...path]/route.ts:77-79
const adminCredentials = {
  email: "admin@jobbot.com",
  password: "JobBotAdmin!2026",  // ❌ HARDCODED - CRITICAL!
  name: "Admin JobBot",
};
```

### Step-by-Step Fix

#### Step 1: Update Environment Variables
```bash
# Add to .env (NEVER commit this file)
ADMIN_EMAIL=admin@jobbot.com
ADMIN_PASSWORD=$(openssl rand -base64 32)  # Generate strong password
ADMIN_NAME="Admin JobBot"
```

#### Step 2: Update Environment Configuration
```typescript
// dashboard/src/lib/env.ts
export const env = {
  ADMIN_EMAIL: process.env.ADMIN_EMAIL || "",
  ADMIN_PASSWORD: process.env.ADMIN_PASSWORD || "",
  ADMIN_NAME: process.env.ADMIN_NAME || "Admin",
} as const;

// Validate on startup
if (process.env.NODE_ENV === "production") {
  if (!env.ADMIN_EMAIL || !env.ADMIN_PASSWORD) {
    throw new Error("Admin credentials not configured");
  }
}
```

#### Step 3: Update Backend Route
```typescript
// dashboard/src/app/api/backend/[...path]/route.ts

// Replace hardcoded object with:
const adminCredentials = {
  email: process.env.ADMIN_EMAIL || "",
  password: process.env.ADMIN_PASSWORD || "",
  name: process.env.ADMIN_NAME || "Admin",
};

// Add validation in build time check
const validateCredentials = () => {
  if (adminCredentials.email === "admin@jobbot.com") {
    throw new Error("Default admin email must be changed");
  }
  if (!adminCredentials.password || adminCredentials.password.length < 16) {
    throw new Error("Admin password must be at least 16 characters");
  }
};
```

#### Step 4: Rotate Credentials
```bash
# 1. Change admin password immediately in production
# 2. Check git history for exposed credentials
git log --all --full-history -- dashboard/src/app/api/backend/

# 3. If credentials were ever committed, consider them COMPROMISED
# Generate new credentials and rotate immediately
```

#### Step 5: Add Git Pre-Commit Hook
```bash
# .husky/pre-commit or .git/hooks/pre-commit
#!/bin/bash
if grep -r "admin@jobbot.com" dashboard/src/ --include="*.ts" --include="*.tsx"; then
  echo "ERROR: Hardcoded admin email detected"
  exit 1
fi

if grep -r "JobBotAdmin!2026" dashboard/src/ --include="*.ts" --include="*.tsx"; then
  echo "ERROR: Hardcoded admin password detected"
  exit 1
fi
```

---

## 🔴 Fix 2: Migrate from localStorage to HttpOnly Cookies

### Current Problem
```typescript
// dashboard/src/lib/api.ts
export function getToken() {
  return localStorage.getItem("token"); // ❌ XSS VULNERABLE
}

export function setToken(token: string) {
  localStorage.setItem("token", token); // ❌ JavaScript accessible
}
```

### Step-by-Step Fix

#### Step 1: Update Backend Login Endpoint
```python
# api/routes/auth.py

from fastapi import Response
from datetime import timedelta

@router.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Database = Depends(get_db),
    response: Response = None,  # Add response parameter
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

    # Create tokens
    access_token = create_access_token(
        data={"sub": email, "telegram_id": user["telegram_id"]}
    )
    
    # Generate refresh token
    refresh_token = create_refresh_token(
        data={"sub": email, "telegram_id": user["telegram_id"]}
    )
    
    # Store refresh token hash in DB
    db.store_refresh_token(
        user_id=user["telegram_id"],
        token_hash=hashlib.sha256(refresh_token.encode()).hexdigest(),
        expires_at=int((datetime.now(timezone.utc) + timedelta(days=7)).timestamp())
    )
    
    # Set httpOnly cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,  # Only HTTPS
        samesite="strict",  # CSRF protection
        max_age=86400,  # 24 hours
        path="/",
    )
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=604800,  # 7 days
        path="/api/auth/refresh",  # Only for refresh endpoint
    )
    
    # Return minimal info (no tokens in body)
    return {
        "message": "Login successful",
        "telegram_id": user["telegram_id"],
        "email": email,
    }
```

#### Step 2: Add Cookie-Based Auth Dependency
```python
# api/routes/auth.py

from fastapi import Cookie

def get_authenticated_user_from_cookie(
    access_token: Optional[str] = Cookie(None),
    db: Database = Depends(get_db)
):
    """Authenticate using httpOnly cookie."""
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    payload = decode_token(access_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired or invalid",
        )
    
    # ... rest of existing get_authenticated_user logic
    telegram_id = payload.get("telegram_id")
    email = payload.get("sub")
    
    # Check blacklist
    if db.is_token_blacklisted(hashlib.sha256(access_token.encode()).hexdigest()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token revoked",
        )
    
    # ... return user dict
```

#### Step 3: Add Refresh Endpoint
```python
@router.post("/auth/refresh")
async def refresh_token(
    refresh_token: Optional[str] = Cookie(None),
    response: Response = None,
    db: Database = Depends(get_db),
):
    """Refresh access token using httpOnly refresh cookie."""
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token",
        )
    
    # Validate refresh token
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    # Check if refresh token is valid in DB
    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    if not db.is_refresh_token_valid(token_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token revoked",
        )
    
    telegram_id = payload.get("telegram_id")
    email = payload.get("sub")
    
    # Create new access token
    new_access_token = create_access_token(
        data={"sub": email, "telegram_id": telegram_id}
    )
    
    # Rotate refresh token (one-time use)
    new_refresh_token = create_refresh_token(
        data={"sub": email, "telegram_id": telegram_id}
    )
    
    # Revoke old refresh token
    db.revoke_refresh_token(token_hash, replaced_by=hashlib.sha256(new_refresh_token.encode()).hexdigest())
    
    # Store new refresh token
    db.store_refresh_token(
        user_id=telegram_id,
        token_hash=hashlib.sha256(new_refresh_token.encode()).hexdigest(),
        expires_at=int((datetime.now(timezone.utc) + timedelta(days=7)).timestamp())
    )
    
    # Set new cookies
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=86400,
        path="/",
    )
    
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=604800,
        path="/api/auth/refresh",
    )
    
    return {"message": "Token refreshed"}
```

#### Step 4: Update Frontend API Client
```typescript
// dashboard/src/lib/api.ts (COMPLETELY REWRITTEN)

export interface ApiError {
  detail?: string;
  message: string;
  status: number;
}

function resolveApiBaseUrl() {
  // Use relative URL - cookies are sent automatically
  return "/api/backend";
}

export function getApiBaseUrl() {
  return resolveApiBaseUrl();
}

/**
 * Make API request with automatic cookie handling.
 * NO TOKEN STORAGE - uses httpOnly cookies only.
 */
export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const apiBaseUrl = resolveApiBaseUrl();

  const headers = new Headers(init.headers ?? {});
  const isFormData = typeof FormData !== "undefined" && init.body instanceof FormData;
  const isUrlEncoded =
    typeof URLSearchParams !== "undefined" && init.body instanceof URLSearchParams;

  // Content-Type for non-file requests
  if (!isFormData && !headers.has("Content-Type") && init.body) {
    headers.set(
      "Content-Type",
      isUrlEncoded ? "application/x-www-form-urlencoded;charset=UTF-8" : "application/json",
    );
  }

  // IMPORTANT: credentials: "include" sends cookies automatically
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    credentials: "include", // ✅ Sends httpOnly cookies
    headers,
  });

  // Handle 401 - token expired, try refresh
  if (response.status === 401 && path !== "/auth/refresh") {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      // Retry original request
      return apiRequest(path, init);
    }
    // Refresh failed - redirect to login
    window.location.href = "/login?expired=1";
    throw { message: "Sesion expirada", status: 401 } satisfies ApiError;
  }

  const contentType = response.headers.get("content-type") ?? "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const detail =
      typeof payload === "string"
        ? payload
        : payload?.detail || payload?.message || "Error inesperado";
    throw {
      detail,
      message: detail,
      status: response.status,
    } satisfies ApiError;
  }

  return payload as T;
}

/**
 * Attempt to refresh access token.
 * Returns true if successful.
 */
async function refreshAccessToken(): Promise<boolean> {
  try {
    const response = await fetch("/api/auth/refresh", {
      method: "POST",
      credentials: "include",
    });
    return response.ok;
  } catch {
    return false;
  }
}

/**
 * Login - credentials handled by server, cookies set automatically.
 */
export async function login(email: string, password: string): Promise<{ success: boolean; error?: string }> {
  try {
    const response = await fetch("/api/auth/token", {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({ username: email, password }),
    });

    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      return { success: false, error: data.detail || "Credenciales invalidas" };
    }

    // Server sets httpOnly cookies automatically
    // We just confirm login was successful
    return { success: true };
  } catch (error) {
    return { success: false, error: "Error de conexion" };
  }
}

/**
 * Logout - clears httpOnly cookies via server.
 */
export async function logout(): Promise<void> {
  try {
    await fetch("/api/auth/logout", {
      method: "POST",
      credentials: "include",
    });
  } finally {
    // Clear any client-side state
    clearAuthState();
    window.location.href = "/login";
  }
}

// Legacy functions - REMOVE THESE
// export function getToken() { ... } ❌ DELETE
// export function setToken(token: string) { ... } ❌ DELETE
// export function clearToken() { ... } ❌ DELETE
```

#### Step 5: Update Login Page
```typescript
// dashboard/src/app/(auth)/login/page.tsx - SIMPLIFIED

const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  setLoading(true);
  setMessage("");

  try {
    const result = await login(email, password);
    
    if (result.success) {
      setAuthState(true); // UI state only - no token!
      router.replace(nextPath);
    } else {
      setMessage(result.error || "Error de autenticacion");
    }
  } catch (error) {
    setMessage("Error de conexion");
  } finally {
    setLoading(false);
  }
};
```

#### Step 6: CORS Configuration Update
```python
# api/main.py - Update CORS to allow credentials

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app-jobbot.vercel.app",
        "https://jobbot.ar",
        # Add other production domains
    ],  # ❌ No wildcards when using credentials!
    allow_credentials=True,  # ✅ Allow cookies
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "X-CSRF-Token"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining"],
)
```

---

## 🔴 Fix 3: Secure JWT Secret Configuration

### Current Problem
```yaml
# docker-compose.yml
environment:
  - JWT_SECRET_KEY=${JWT_SECRET_KEY:-change-me-in-production}  # ❌ Weak default
```

### Step-by-Step Fix

#### Step 1: Remove Default Secret
```yaml
# docker-compose.yml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}  # ✅ No default - must be set
      - TELEGRAM_TOKEN=${TELEGRAM_TOKEN}
      - GROQ_API_KEY=${GROQ_API_KEY}
    env_file:
      - .env
    volumes:
      - ./job_bot:/app/job_bot
      - ./api:/app/api
    restart: unless-stopped
```

#### Step 2: Add Startup Validation
```python
# api/core/security.py

def validate_jwt_secret() -> str:
    """
    Validate JWT secret configuration.
    Raises RuntimeError if secret is missing or weak.
    """
    secret = os.getenv("JWT_SECRET_KEY")
    
    # Check existence
    if not secret:
        error_msg = """
╔════════════════════════════════════════════════════════════════╗
║  FATAL: JWT_SECRET_KEY not configured                         ║
║                                                                ║
║  Generate a secure secret with:                                 ║
║    openssl rand -hex 32                                        ║
║                                                                ║
║  Or use a password manager to generate 64+ random chars.       ║
╚════════════════════════════════════════════════════════════════╝
        """
        raise RuntimeError(error_msg)
    
    # Check minimum length
    if len(secret) < 32:
        raise RuntimeError(
            f"JWT_SECRET_KEY must be at least 32 characters (got {len(secret)})"
        )
    
    # Check for common weak secrets
    weak_patterns = [
        "change-me",
        "secret",
        "password",
        "123456",
        "admin",
        "default",
    ]
    
    secret_lower = secret.lower()
    for pattern in weak_patterns:
        if pattern in secret_lower:
            raise RuntimeError(
                f"JWT_SECRET_KEY appears to be a weak/default value. "
                f"Detected pattern: '{pattern}'"
            )
    
    # Check entropy (basic check for repeated characters)
    unique_chars = len(set(secret))
    if unique_chars < 10:
        raise RuntimeError(
            f"JWT_SECRET_KEY has low entropy (only {unique_chars} unique characters). "
            "Generate a more random secret."
        )
    
    return secret


# Run validation at import time
JWT_SECRET_KEY = validate_jwt_secret()
```

#### Step 3: Add Production Check to Main
```python
# api/main.py

@app.on_event("startup")
async def startup_validation():
    """Validate security configuration on startup."""
    app_env = os.getenv("APP_ENV", "development").lower()
    
    if app_env == "production":
        required_secrets = [
            "JWT_SECRET_KEY",
            "STRIPE_SECRET_KEY",
            "DATABASE_URL",
            "TELEGRAM_TOKEN",
        ]
        
        missing = [s for s in required_secrets if not os.getenv(s)]
        
        if missing:
            logger.error(f"Missing required secrets: {missing}")
            raise RuntimeError(
                f"Cannot start in production. Missing: {', '.join(missing)}"
            )
        
        # Validate JWT secret strength
        jwt_secret = os.getenv("JWT_SECRET_KEY", "")
        if len(jwt_secret) < 32:
            raise RuntimeError(
                "JWT_SECRET_KEY must be at least 32 characters in production"
            )
        
        logger.info("✅ Production security validation passed")
```

#### Step 4: Create Secret Generation Script
```python
#!/usr/bin/env python3
"""Generate secure secrets for JobBot deployment."""

import secrets
import sys

def generate_secret(length: int = 64) -> str:
    """Generate a cryptographically secure random secret."""
    return secrets.token_urlsafe(length)

def main():
    print("# JobBot Environment Configuration")
    print("# Add these to your .env file (NEVER commit .env!)")
    print()
    
    # JWT Secret (minimum 32 chars, we generate 64)
    jwt_secret = generate_secret(48)  # ~64 chars
    print(f"JWT_SECRET_KEY={jwt_secret}")
    
    # Other secrets
    print(f"# Generate additional secrets as needed:")
    print(f"# TELEGRAM_TOKEN=your_telegram_bot_token")
    print(f"# STRIPE_SECRET_KEY=sk_test_...")
    
    print()
    print("# ✅ Generated secrets are cryptographically secure")
    print("# 🔒 Store safely in your password manager or secrets manager")
    
    # Validate
    if len(jwt_secret) < 32:
        print("ERROR: Generated secret too short!")
        sys.exit(1)
    
    print(f"\n# JWT secret length: {len(jwt_secret)} characters ✓")

if __name__ == "__main__":
    main()
```

#### Step 5: Document Secret Management
```markdown
# SECRET_MANAGEMENT.md

## Required Secrets

| Secret | Length | Environment | Notes |
|--------|--------|-------------|-------|
| JWT_SECRET_KEY | 32+ chars | All | Used for token signing |
| DATABASE_URL | - | All | PostgreSQL connection |
| STRIPE_SECRET_KEY | - | Production | Payment processing |
| TELEGRAM_TOKEN | - | All | Bot authentication |

## Generating Secrets

```bash
# JWT Secret
openssl rand -hex 32

# Or using Python
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

## Storage

- Development: `.env` file (gitignored)
- Production: Use secrets manager (Vercel, Railway, AWS Secrets Manager)
- Never commit secrets to git
- Rotate secrets every 90 days

## Validation

The application will refuse to start if:
- JWT_SECRET_KEY is not set
- JWT_SECRET_KEY is < 32 characters
- JWT_SECRET_KEY contains weak patterns
```

---

## Testing the Fixes

### Test 1: Verify No Hardcoded Credentials
```bash
# Search for hardcoded patterns
grep -r "admin@jobbot.com" dashboard/ || echo "✅ No hardcoded email found"
grep -r "JobBotAdmin" dashboard/ || echo "✅ No hardcoded password found"
grep -r "password.*=" dashboard/src/ | grep -v "process.env" | grep -v "password_hash"
```

### Test 2: Verify HttpOnly Cookies
```bash
# 1. Login via API
curl -c cookies.txt -X POST http://localhost:8000/auth/token \
  -d "username=test@example.com" \
  -d "password=testpass"

# 2. Verify cookie is set
cat cookies.txt | grep "access_token"
# Should show: access_token with HttpOnly flag

# 3. Try to access cookie via JavaScript (in browser console)
document.cookie  // Should NOT show access_token
```

### Test 3: Verify JWT Secret Validation
```bash
# 1. Without secret - should fail
unset JWT_SECRET_KEY
python -c "from api.core.security import validate_jwt_secret"
# Expected: RuntimeError: FATAL: JWT_SECRET_KEY not configured

# 2. With weak secret - should fail
JWT_SECRET_KEY="weak" python -c "from api.core.security import validate_jwt_secret"
# Expected: RuntimeError: must be at least 32 characters

# 3. With strong secret - should pass
JWT_SECRET_KEY="$(openssl rand -hex 32)" python -c "from api.core.security import validate_jwt_secret; print('✅ Valid')"
```

### Test 4: XSS Protection
```bash
# Attempt XSS payload in login
curl -X POST http://localhost:8000/auth/token \
  -d "username=<script>alert(1)</script>" \
  -d "password=test"
# Should be sanitized or rejected
```

---

## Deployment Checklist

- [ ] Hardcoded credentials removed from route.ts
- [ ] New admin credentials generated and stored securely
- [ ] HttpOnly cookie implementation deployed
- [ ] Frontend localStorage token storage removed
- [ ] JWT secret validation active
- [ ] Production secrets configured in hosting platform
- [ ] Old JWT secrets rotated
- [ ] Smoke tests passing
- [ ] Security regression tests passing

---

*Fixes prepared by OpenCode Security Agent*

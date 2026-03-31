import json
import logging
import os
import time

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .rate_limit import (
    API_LIMIT,
    API_WINDOW_SECONDS,
    LOGIN_LIMIT,
    LOGIN_WINDOW_SECONDS,
    rate_limiter,
)
from .routes import auth, cv, jobs, public, subscriptions, users


logger = logging.getLogger("jobbot.api")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


def _cors_origins() -> list[str]:
    configured = [
        origin.strip()
        for origin in (os.getenv("CORS_ORIGINS", "")).split(",")
        if origin.strip()
    ]
    if configured:
        return configured

    return [
        "http://localhost:3000",
        "http://localhost:3010",
        "http://localhost:3011",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3010",
        "http://127.0.0.1:3011",
        "https://tu-dominio.com",
        "https://jobbot.ar",
    ]

app = FastAPI(
    title="JobBot API", version="1.0.0", description="API para el servicio JobBot SaaS"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@app.middleware("http")
async def logging_and_rate_limit_middleware(request: Request, call_next):
    started = time.time()
    path = request.url.path
    method = request.method
    ip = _client_ip(request)

    headers = {}
    if path == "/auth/token" and method == "POST":
        allowed, remaining, retry_after = rate_limiter.check(
            f"login:{ip}", LOGIN_LIMIT, LOGIN_WINDOW_SECONDS
        )
        headers = {
            "X-RateLimit-Limit": str(LOGIN_LIMIT),
            "X-RateLimit-Remaining": str(remaining),
        }
        if not allowed:
            headers["Retry-After"] = str(retry_after)
            return JSONResponse(
                status_code=429,
                content={"detail": "Demasiados intentos de login. Intenta mas tarde."},
                headers=headers,
            )
    elif not path.startswith("/health") and not path.startswith("/stats"):
        auth_header = request.headers.get("authorization", "")
        identity = auth_header or ip
        allowed, remaining, retry_after = rate_limiter.check(
            f"api:{identity}", API_LIMIT, API_WINDOW_SECONDS
        )
        headers = {
            "X-RateLimit-Limit": str(API_LIMIT),
            "X-RateLimit-Remaining": str(remaining),
        }
        if not allowed:
            headers["Retry-After"] = str(retry_after)
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit excedido."},
                headers=headers,
            )

    try:
        response = await call_next(request)
    except Exception as exc:
        duration_ms = round((time.time() - started) * 1000, 2)
        logger.error(
            json.dumps(
                {
                    "event": "request_error",
                    "method": method,
                    "path": path,
                    "ip": ip,
                    "duration_ms": duration_ms,
                    "error_type": exc.__class__.__name__,
                }
            )
        )
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    duration_ms = round((time.time() - started) * 1000, 2)
    for key, value in headers.items():
        response.headers[key] = value

    logger.info(
        json.dumps(
            {
                "event": "http_request",
                "method": method,
                "path": path,
                "status_code": response.status_code,
                "ip": ip,
                "duration_ms": duration_ms,
            }
        )
    )
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
app.include_router(cv.router, prefix="/cv", tags=["cv"])
app.include_router(public.router, tags=["public"])


@app.get("/")
def root():
    return {"message": "JobBot API", "version": "1.0.0"}

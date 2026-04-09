"""
Rate limiting middleware for JobBot API.

Applies the shared endpoint rate limit rules before hitting route handlers,
and uses a token-derived identity when available so authenticated flows are
limited per user instead of only by IP.
"""

import os

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

try:
    from ..core.security import decode_token as security_decode_token
except ImportError:
    from api.core.security import decode_token as security_decode_token

from ..rate_limit import (
    check_rate_limit,
    get_client_ip,
    is_exempt_from_rate_limit,
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Shared API rate limiting middleware."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method
        trace_id = getattr(request.state, "trace_id", None)
        if not trace_id:
            trace_id = request.headers.get("x-trace-id") or os.urandom(16).hex()
        request.state.trace_id = trace_id

        if is_exempt_from_rate_limit(path, method):
            return await call_next(request)

        identity = f"ip:{get_client_ip(request)}"
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:].strip()
            if token:
                payload = security_decode_token(token)
                telegram_id = payload.get("telegram_id") if payload else None
                if telegram_id is not None:
                    try:
                        request.state.user_id = int(telegram_id)
                        identity = f"user:{int(telegram_id)}"
                    except (TypeError, ValueError):
                        request.state.user_id = None

        allowed, headers = check_rate_limit(path, method, identity)
        if not allowed:
            response = JSONResponse(
                status_code=429,
                content={
                    "detail": "Demasiadas solicitudes. Intenta de nuevo en unos segundos.",
                    "trace_id": getattr(request.state, "trace_id", "unknown"),
                },
                headers=headers,
            )
            origin = request.headers.get("origin")
            if origin:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Vary"] = "Origin"
                response.headers["Access-Control-Allow-Credentials"] = "true"
            return response

        response = await call_next(request)
        for header_name, header_value in headers.items():
            response.headers.setdefault(header_name, header_value)
        return response

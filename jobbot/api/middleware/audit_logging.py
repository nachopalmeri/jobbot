"""
Audit Logging Middleware for JobBot API
Logs all HTTP requests with user ID, endpoint, method, timestamp, IP, and response status.
"""

import json
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


def _client_ip(request: Request) -> str:
    """Extract client IP from request headers or connection."""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _extract_user_id(request: Request) -> Optional[int]:
    """Extract user ID from request state if available."""
    # This will be populated by auth middleware
    return getattr(request.state, "user_id", None)


class AuditLogMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs all HTTP requests to the audit_logs table.
    """
    
    def __init__(self, app, database=None):
        super().__init__(app)
        self.database = database
    
    async def dispatch(self, request: Request, call_next):
        # Record start time
        start_time = time.time()
        
        # Extract request info before processing
        ip_address = _client_ip(request)
        method = request.method
        endpoint = str(request.url.path)
        
        # Get user ID from state (set by auth middleware)
        user_id = _extract_user_id(request)
        
        # Process the request
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            status_code = 500
            raise exc
        finally:
            # Calculate duration
            duration_ms = round((time.time() - start_time) * 1000, 2)
            
            # Log to database (non-blocking, don't fail the request)
            try:
                self._log_audit_entry(
                    user_id=user_id,
                    endpoint=endpoint,
                    method=method,
                    ip_address=ip_address,
                    status_code=status_code,
                    duration_ms=duration_ms,
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
            except Exception as e:
                # Log errors silently to avoid breaking requests
                import logging
                logging.getLogger("jobbot.audit").error(f"Failed to log audit entry: {e}")
        
        return response
    
    def _log_audit_entry(
        self,
        user_id: Optional[int],
        endpoint: str,
        method: str,
        ip_address: str,
        status_code: int,
        duration_ms: float,
        timestamp: str
    ):
        """Store audit log entry in database."""
        if self.database is None:
            return
        
        try:
            self.database.create_audit_log(
                user_id=user_id,
                endpoint=endpoint,
                method=method,
                ip_address=ip_address,
                status_code=status_code,
                duration_ms=duration_ms,
                timestamp=timestamp
            )
        except Exception:
            # Don't let audit logging failures break the API
            pass


class AsyncAuditLogMiddleware:
    """
    Alternative async-friendly middleware for audit logging.
    Can be used as a FastAPI dependency or middleware.
    """
    
    def __init__(self, database=None):
        self.database = database
    
    async def log_request(
        self,
        request: Request,
        response: Response,
        user_id: Optional[int] = None,
        duration_ms: float = 0.0
    ):
        """Log a request/response pair."""
        if self.database is None:
            return
        
        try:
            self.database.create_audit_log(
                user_id=user_id,
                endpoint=str(request.url.path),
                method=request.method,
                ip_address=_client_ip(request),
                status_code=response.status_code,
                duration_ms=duration_ms,
                timestamp=datetime.now(timezone.utc).isoformat()
            )
        except Exception:
            pass


def get_audit_logger(database=None):
    """Factory function to create an audit logger instance."""
    return AsyncAuditLogMiddleware(database)

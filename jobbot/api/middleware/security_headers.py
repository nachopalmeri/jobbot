"""
Security Headers Middleware for JobBot API
Implements Content Security Policy and other security headers.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


# Content Security Policy directives
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: https:; "
    "font-src 'self'; "
    "connect-src 'self'; "
    "media-src 'self'; "
    "object-src 'none'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self';"
)

# Security headers configuration
SECURITY_HEADERS = {
    # Prevent MIME type sniffing
    "X-Content-Type-Options": "nosniff",
    
    # Prevent clickjacking
    "X-Frame-Options": "DENY",
    
    # XSS protection (legacy but still useful)
    "X-XSS-Protection": "1; mode=block",
    
    # HSTS - HTTPS only
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    
    # Referrer policy
    "Referrer-Policy": "strict-origin-when-cross-origin",
    
    # Permissions policy
    "Permissions-Policy": (
        "accelerometer=(), "
        "camera=(), "
        "geolocation=(), "
        "gyroscope=(), "
        "magnetometer=(), "
        "microphone=(), "
        "payment=(), "
        "usb=()"
    ),
    
    # Content Security Policy
    "Content-Security-Policy": CONTENT_SECURITY_POLICY,
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds security headers to all responses.
    Includes CSP, HSTS, X-Frame-Options, and other security headers.
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers to all responses
        for header_name, header_value in SECURITY_HEADERS.items():
            response.headers[header_name] = header_value
        
        return response


class SecurityHeadersDependency:
    """
    Dependency-based approach for adding security headers.
    Can be used as a FastAPI dependency on specific routes.
    """
    
    def __init__(self):
        self.headers = SECURITY_HEADERS.copy()
    
    def apply_headers(self, response: Response):
        """Apply security headers to a response object."""
        for header_name, header_value in self.headers.items():
            response.headers[header_name] = header_value
        return response
    
    def __call__(self, response: Response):
        """Callable interface for use as FastAPI dependency."""
        return self.apply_headers(response)


def get_security_headers():
    """Factory function to get security headers configuration."""
    return SECURITY_HEADERS.copy()


def add_security_headers(response: Response) -> Response:
    """Utility function to add security headers to a response."""
    for header_name, header_value in SECURITY_HEADERS.items():
        response.headers[header_name] = header_value
    return response

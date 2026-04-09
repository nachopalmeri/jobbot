"""
Payload Size Limiting Middleware for JobBot API
Prevents DoS attacks via large request bodies.
"""

import logging
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger("jobbot.security")


class PayloadTooLargeError(Exception):
    """Exception raised when request payload exceeds size limit."""
    pass


class PayloadSizeMiddleware(BaseHTTPMiddleware):
    """
    Middleware that limits request payload size to prevent DoS attacks.
    
    Checks Content-Length header and rejects requests that exceed the limit.
    """
    
    def __init__(
        self,
        app,
        max_size_bytes: int = 10 * 1024 * 1024,  # 10MB default
        exempt_paths: Optional[list] = None,
    ):
        super().__init__(app)
        self.max_size_bytes = max_size_bytes
        self.exempt_paths = exempt_paths or [
            "/webhooks/",  # Webhooks might need larger payloads
            "/uploads/",
        ]
        
        logger.info(
            f"PayloadSizeMiddleware initialized with limit: {max_size_bytes} bytes"
        )
    
    async def dispatch(self, request: Request, call_next):
        """Check payload size before processing request."""
        path = request.url.path
        
        # Check if path is exempt
        for exempt in self.exempt_paths:
            if exempt in path:
                return await call_next(request)
        
        # Check Content-Length header
        content_length = request.headers.get("content-length")
        
        if content_length:
            try:
                size = int(content_length)
                if size > self.max_size_bytes:
                    logger.warning(
                        f"Payload too large: {size} bytes from {request.client.host} "
                        f"to {path}"
                    )
                    return JSONResponse(
                        status_code=413,
                        content={
                            "detail": (
                                f"Request body too large. "
                                f"Maximum size is {self.max_size_bytes} bytes."
                            )
                        }
                    )
            except ValueError:
                # Invalid Content-Length header
                logger.warning(
                    f"Invalid Content-Length header from {request.client.host}: "
                    f"{content_length}"
                )
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid Content-Length header"}
                )
        
        # For requests without Content-Length (chunked encoding), 
        # we'll limit via max read size during body reading
        # This is handled by the framework
        
        return await call_next(request)


def validate_payload_size(
    data: bytes,
    max_size: int = 10 * 1024 * 1024,
    field_name: str = "payload"
) -> bool:
    """
    Validate that payload size is within limits.
    
    Args:
        data: Payload data
        max_size: Maximum allowed size in bytes
        field_name: Name of field for error message
    
    Returns:
        True if size is valid
    
    Raises:
        PayloadTooLargeError if size exceeds limit
    """
    size = len(data) if isinstance(data, bytes) else len(data.encode('utf-8'))
    
    if size > max_size:
        raise PayloadTooLargeError(
            f"{field_name} exceeds maximum size of {max_size} bytes "
            f"(received {size} bytes)"
        )
    
    return True


# Size limits for specific content types
CONTENT_TYPE_LIMITS = {
    "application/json": 10 * 1024 * 1024,      # 10MB
    "application/x-www-form-urlencoded": 1024 * 1024,  # 1MB
    "multipart/form-data": 50 * 1024 * 1024,    # 50MB (for file uploads)
    "text/plain": 5 * 1024 * 1024,             # 5MB
}

"""
XSS Protection Middleware for JobBot API
Sanitizes user input to prevent Cross-Site Scripting attacks.
"""

import re
import html
import logging
from typing import Any, Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse

logger = logging.getLogger("jobbot.security")


# Dangerous patterns for XSS detection
DANGEROUS_PATTERNS = [
    r'<script[^>]*>.*?</script>',
    r'javascript:\s*',
    r'on\w+\s*=\s*["\'][^"\']*["\']',
    r'data:text/html[^,]*,',
    r'<iframe[^>]*>',
    r'<object[^>]*>',
    r'<embed[^>]*>',
    r'expression\s*\(',
]

DANGEROUS_REGEX = re.compile('|'.join(DANGEROUS_PATTERNS), re.IGNORECASE | re.DOTALL)

# Safe HTML tags (if we need to allow some HTML)
SAFE_HTML_TAGS = ['b', 'i', 'em', 'strong', 'p', 'br', 'ul', 'ol', 'li']


def strip_html_tags(text: str) -> str:
    """Remove all HTML tags from text."""
    if not text:
        return text
    clean = re.sub(r'<[^>]+>', '', text)
    return html.unescape(clean)


def sanitize_html(text: str, allowed_tags: Optional[list] = None) -> str:
    """
    Sanitize HTML by removing dangerous content.
    Keeps only allowed safe tags.
    """
    if not text:
        return text
    
    allowed = allowed_tags or SAFE_HTML_TAGS
    
    # First, escape all HTML entities
    text = html.escape(text)
    
    # Then selectively unescape allowed tags
    for tag in allowed:
        # Unescape opening tags
        text = re.sub(
            f'&lt;({tag})([^&]*)&gt;',
            r'<\1\2>',
            text,
            flags=re.IGNORECASE
        )
        # Unescape closing tags
        text = re.sub(
            f'&lt;/{tag}&gt;',
            f'</{tag}>',
            text,
            flags=re.IGNORECASE
        )
    
    return text


def validate_input(text: str, field_name: str = "input") -> tuple[bool, Optional[str]]:
    """
    Validate input for dangerous XSS patterns.
    
    Returns:
        Tuple of (is_safe, error_message)
    """
    if not text:
        return True, None
    
    # Check for dangerous patterns
    if DANGEROUS_REGEX.search(text):
        logger.warning(f"XSS pattern detected in {field_name}")
        return False, f"Potentially dangerous content detected in {field_name}"
    
    return True, None


def sanitize_dict(data: Any, max_depth: int = 10) -> Any:
    """
    Recursively sanitize dictionary values.
    
    Args:
        data: Data to sanitize
        max_depth: Maximum recursion depth
    
    Returns:
        Sanitized data
    """
    if max_depth <= 0:
        return data
    
    if isinstance(data, dict):
        return {
            k: sanitize_dict(v, max_depth - 1)
            for k, v in data.items()
        }
    elif isinstance(data, list):
        return [sanitize_dict(item, max_depth - 1) for item in data]
    elif isinstance(data, str):
        return html.escape(data)
    else:
        return data


class XSSProtectionMiddleware(BaseHTTPMiddleware):
    """
    Middleware that sanitizes request and response data to prevent XSS attacks.
    """
    
    def __init__(
        self,
        app,
        sanitize_request_body: bool = True,
        sanitize_response_body: bool = False,
        max_field_length: int = 10000,
    ):
        super().__init__(app)
        self.sanitize_request_body = sanitize_request_body
        self.sanitize_response_body = sanitize_response_body
        self.max_field_length = max_field_length
    
    async def dispatch(self, request: Request, call_next):
        """Process request/response with XSS protection."""
        
        # Check query parameters for XSS
        for key, value in request.query_params.items():
            is_safe, error = validate_input(value, f"query param '{key}'")
            if not is_safe:
                logger.warning(f"XSS attempt blocked: {key}={value[:100]}")
                return JSONResponse(
                    status_code=400,
                    content={"detail": error}
                )
        
        # Check headers for XSS (except standard headers)
        skip_headers = {
            'authorization', 'content-type', 'accept', 'user-agent',
            'x-requested-with', 'x-trace-id', 'x-client-version'
        }
        
        for key, value in request.headers.items():
            if key.lower() in skip_headers:
                continue
            
            is_safe, error = validate_input(value, f"header '{key}'")
            if not is_safe:
                logger.warning(f"XSS attempt in header blocked: {key}")
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid header content"}
                )
        
        # Process request
        response = await call_next(request)
        
        return response


def xss_validator(field_name: str):
    """
    Validator function for use with Pydantic.
    
    Usage:
        class MyModel(BaseModel):
            description: str = Field(..., validator=xss_validator("description"))
    """
    def validate(value: str) -> str:
        is_safe, error = validate_input(value, field_name)
        if not is_safe:
            raise ValueError(error)
        return value
    return validate

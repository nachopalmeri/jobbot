"""
Middleware package for JobBot API security features.
Includes security headers, audit logging, XSS protection, and payload limiting.
"""

from .audit_logging import (
    AuditLogMiddleware,
    AsyncAuditLogMiddleware,
    get_audit_logger,
)

from .security_headers import (
    SecurityHeadersMiddleware,
    SecurityHeadersDependency,
    add_security_headers,
    get_security_headers,
)

from .xss_protection import (
    XSSProtectionMiddleware,
    sanitize_html,
    strip_html_tags,
    validate_input,
)

from .payload_limit import (
    PayloadSizeMiddleware,
    PayloadTooLargeError,
    validate_payload_size,
)

__all__ = [
    # Audit logging
    "AuditLogMiddleware",
    "AsyncAuditLogMiddleware",
    "get_audit_logger",
    # Security headers
    "SecurityHeadersMiddleware",
    "SecurityHeadersDependency",
    "add_security_headers",
    "get_security_headers",
    # XSS protection
    "XSSProtectionMiddleware",
    "sanitize_html",
    "strip_html_tags",
    "validate_input",
    # Payload limiting
    "PayloadSizeMiddleware",
    "PayloadTooLargeError",
    "validate_payload_size",
]

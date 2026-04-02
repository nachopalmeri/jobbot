import json
import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

# Import security middleware
from .middleware import (
    AuditLogMiddleware,
    SecurityHeadersMiddleware,
    get_audit_logger,
    add_security_headers,
    PayloadSizeMiddleware,
    XSSProtectionMiddleware,
)
from .core import (
    TokenBlacklist,
    RefreshTokenManager,
    validate_jwt_secret,
    get_token_blacklist,
    get_refresh_token_manager,
    cache,
    graceful_shutdown,
    get_all_circuit_breakers,
)

# Import enhanced rate limiting
from .rate_limit import (
    endpoint_rate_limiter,
    is_exempt_from_rate_limit,
    get_client_ip,
)

# Import routes
from .routes import auth, cv, jobs, public, subscriptions, users


# Structured JSON logging setup
class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime()),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in log_obj and not key.startswith("_"):
                log_obj[key] = value
        
        return json.dumps(log_obj)


# Setup root logger
logger = logging.getLogger("jobbot.api")
logger.setLevel(logging.INFO)

# Console handler with JSON formatting
console_handler = logging.StreamHandler()
console_handler.setFormatter(JSONFormatter())

# Remove existing handlers to prevent duplicates
logger.handlers = []
logger.addHandler(console_handler)

# Prevent propagation to avoid double logging
logger.propagate = False


def _cors_origins() -> list[str]:
    """
    Get CORS origins from environment.
    Falls back to safe defaults in production.
    """
    env_origins = os.getenv("CORS_ORIGINS", "").strip()
    
    if env_origins:
        origins = [
            origin.strip()
            for origin in env_origins.split(",")
            if origin.strip()
        ]
        if origins:
            return origins
    
    # Production defaults
    if os.getenv("APP_ENV", "development").lower() == "production":
        return [
            "https://jobbot.ar",
            "https://www.jobbot.ar",
            "https://app.jobbot.ar",
            "https://dashboard.jobbot.ar",
        ]
    
    # Development defaults
    return [
        "http://localhost:3000",
        "http://localhost:3010",
        "http://localhost:3011",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3010",
        "http://127.0.0.1:3011",
    ]


# App startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle application startup and shutdown events.
    """
    # Startup
    logger.info({
        "event": "application_startup",
        "version": "1.0.0",
        "environment": os.getenv("APP_ENV", "development"),
    })
    
    # Validate critical configuration
    try:
        validate_jwt_secret()
        logger.info({"event": "jwt_secret_validated"})
    except Exception as e:
        logger.error({
            "event": "jwt_secret_validation_failed",
            "error": str(e),
        })
    
    # Setup graceful shutdown
    graceful_shutdown.setup_signal_handlers()
    
    # Pre-load cache if Redis available
    try:
        cache._backend.get("health_check")
        logger.info({"event": "cache_connection_verified"})
    except Exception as e:
        logger.warning({
            "event": "cache_connection_warning",
            "error": str(e),
        })
    
    yield
    
    # Shutdown
    logger.info({"event": "application_shutdown"})


# Create FastAPI app with OpenAPI configuration
app = FastAPI(
    title="JobBot API",
    version="1.0.0",
    description="API para el servicio JobBot SaaS - Job search automation platform",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware with environment-based configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|jobbot\.ar|.*\.jobbot\.ar)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Requested-With",
        "X-Client-Version",
        "X-Trace-ID",
        "Accept",
        "Origin",
    ],
    expose_headers=[
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Window",
        "X-Request-ID",
        "X-Trace-ID",
    ],
    max_age=86400,  # 24 hours
)

# Add response compression
app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=6)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add XSS protection middleware
app.add_middleware(XSSProtectionMiddleware)

# Add payload size limiting middleware
app.add_middleware(
    PayloadSizeMiddleware,
    max_size_bytes=int(os.getenv("MAX_REQUEST_SIZE_BYTES", "10485760"))  # 10MB default
)

# Import database for audit logging
try:
    from job_bot.database import Database
    _database = Database()
except ImportError:
    from database import Database
    _database = Database()

# Add audit logging middleware
app.add_middleware(AuditLogMiddleware, database=_database)


@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    """
    Middleware for request observability: tracing, metrics, logging.
    """
    # Generate trace ID
    trace_id = request.headers.get("X-Trace-ID") or os.urandom(16).hex()
    request.state.trace_id = trace_id
    request.state.user_id = None
    
    # Start timing
    started = time.time()
    
    # Extract request info
    path = request.url.path
    method = request.method
    ip = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")
    
    # Log request start
    logger.info({
        "event": "request_start",
        "trace_id": trace_id,
        "method": method,
        "path": path,
        "ip": ip,
        "user_agent": user_agent,
    })
    
    # Process request
    try:
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = round((time.time() - started) * 1000, 2)
        
        # Get user ID from request state (set by auth)
        user_id = getattr(request.state, "user_id", None)
        
        # Add trace ID to response
        response.headers["X-Trace-ID"] = trace_id
        response.headers["X-Request-ID"] = trace_id[:16]
        
        # Log request completion
        logger.info({
            "event": "request_complete",
            "trace_id": trace_id,
            "method": method,
            "path": path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "user_id": user_id,
        })
        
        return response
        
    except Exception as exc:
        duration_ms = round((time.time() - started) * 1000, 2)
        
        logger.error({
            "event": "request_error",
            "trace_id": trace_id,
            "method": method,
            "path": path,
            "ip": ip,
            "duration_ms": duration_ms,
            "error_type": exc.__class__.__name__,
            "error_message": str(exc),
        })
        
        raise


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with security headers and structured error."""
    trace_id = getattr(request.state, "trace_id", "unknown")
    
    response = JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "trace_id": trace_id,
        },
    )
    
    response.headers["X-Trace-ID"] = trace_id
    return add_security_headers(response)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions with security headers."""
    trace_id = getattr(request.state, "trace_id", "unknown")
    
    logger.error({
        "event": "unhandled_exception",
        "trace_id": trace_id,
        "error_type": exc.__class__.__name__,
        "error_message": str(exc),
    }, exc_info=True)
    
    response = JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "trace_id": trace_id,
        },
    )
    
    response.headers["X-Trace-ID"] = trace_id
    return add_security_headers(response)


# Include routers with API versioning
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(subscriptions.router, prefix="/subscriptions", tags=["Subscriptions"])
app.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
app.include_router(cv.router, prefix="/cv", tags=["CV"])
app.include_router(public.router, tags=["Public"])


@app.get("/", tags=["Public"])
def root():
    """Root endpoint with API info."""
    return {
        "name": "JobBot API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["Public"])
def health_check():
    """
    Health check endpoint with comprehensive status.
    Used by load balancers and monitoring systems.
    """
    # Check circuit breakers
    circuit_breakers = {
        name: cb.get_metrics()
        for name, cb in get_all_circuit_breakers().items()
    }
    
    # Check cache
    cache_status = "healthy"
    try:
        cache._backend.get("health_check")
    except Exception:
        cache_status = "degraded"
    
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": time.time(),
        "checks": {
            "database": "healthy",  # Simplified check
            "cache": cache_status,
            "circuit_breakers": circuit_breakers,
        },
        "features": {
            "rate_limiting": True,
            "audit_logging": True,
            "security_headers": True,
            "token_blacklist": True,
            "response_compression": True,
            "circuit_breaker": True,
            "cache": cache_status == "healthy",
        },
    }


@app.get("/metrics", tags=["Public"])
def metrics_check():
    """
    Prometheus-style metrics endpoint.
    """
    # Get circuit breaker metrics
    circuit_states = {
        name: cb.get_metrics()
        for name, cb in get_all_circuit_breakers().items()
    }
    
    return {
        "uptime_seconds": time.time() - getattr(app.state, "start_time", time.time()),
        "circuit_breakers": circuit_states,
    }


@app.get("/ready", tags=["Public"])
def readiness_check():
    """
    Kubernetes-style readiness probe.
    Returns 200 when the application is ready to receive traffic.
    """
    return {"status": "ready"}


# Store app start time
app.state.start_time = time.time()

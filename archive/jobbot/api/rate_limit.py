"""
Enhanced Rate Limiting for JobBot API
Implements per-endpoint and per-user rate limiting.
"""

import os
import logging
import threading
import time
from collections import defaultdict, deque
from enum import Enum
from typing import Dict, Optional, Tuple
from uuid import uuid4


logger = logging.getLogger(__name__)


class RateLimitRule:
    """Defines a rate limit rule with limit count and window seconds."""
    
    def __init__(self, limit: int, window_seconds: int, description: str = ""):
        self.limit = limit
        self.window_seconds = window_seconds
        self.description = description


class RateLimitCategory(Enum):
    """Rate limit categories for different endpoint types."""
    LOGIN = "login"
    REGISTER = "register"
    SEARCH = "search"
    CV = "cv"
    TELEGRAM = "telegram"
    DASHBOARD = "dashboard"
    WEBHOOKS = "webhooks"
    API_GENERAL = "api_general"
    PASSWORD_RESET = "password_reset"
    SENSITIVE = "sensitive"


# Default rate limit rules
DEFAULT_RULES = {
    RateLimitCategory.LOGIN: RateLimitRule(
        limit=int(os.getenv("LOGIN_RATE_LIMIT", "5")),
        window_seconds=int(os.getenv("LOGIN_RATE_WINDOW_SECONDS", str(60))),
        description="5 requests per minute for login endpoints"
    ),
    RateLimitCategory.REGISTER: RateLimitRule(
        limit=int(os.getenv("REGISTER_RATE_LIMIT", "3")),
        window_seconds=int(os.getenv("REGISTER_RATE_WINDOW_SECONDS", str(60))),
        description="3 requests per minute for registration"
    ),
    RateLimitCategory.SEARCH: RateLimitRule(
        limit=int(os.getenv("SEARCH_RATE_LIMIT", "20")),
        window_seconds=int(os.getenv("SEARCH_RATE_WINDOW_SECONDS", str(60))),
        description="20 requests per minute for search and preview flows"
    ),
    RateLimitCategory.CV: RateLimitRule(
        limit=int(os.getenv("CV_RATE_LIMIT", "6")),
        window_seconds=int(os.getenv("CV_RATE_WINDOW_SECONDS", str(60))),
        description="6 requests per minute for CV sensitive flows"
    ),
    RateLimitCategory.TELEGRAM: RateLimitRule(
        limit=int(os.getenv("TELEGRAM_RATE_LIMIT", "10")),
        window_seconds=int(os.getenv("TELEGRAM_RATE_WINDOW_SECONDS", str(60))),
        description="10 requests per minute for Telegram linking flows"
    ),
    RateLimitCategory.DASHBOARD: RateLimitRule(
        limit=int(os.getenv("DASHBOARD_RATE_LIMIT", "30")),
        window_seconds=int(os.getenv("DASHBOARD_RATE_WINDOW_SECONDS", str(60))),
        description="30 requests per minute for dashboard-sensitive reads"
    ),
    RateLimitCategory.WEBHOOKS: RateLimitRule(
        limit=int(os.getenv("WEBHOOK_RATE_LIMIT", "100")),
        window_seconds=int(os.getenv("WEBHOOK_RATE_WINDOW_SECONDS", str(60))),
        description="100 requests per minute for webhooks"
    ),
    RateLimitCategory.API_GENERAL: RateLimitRule(
        limit=int(os.getenv("API_RATE_LIMIT", "1000")),
        window_seconds=int(os.getenv("API_RATE_WINDOW_SECONDS", str(3600))),
        description="1000 requests per hour for general API"
    ),
    RateLimitCategory.PASSWORD_RESET: RateLimitRule(
        limit=3,
        window_seconds=3600,
        description="3 password reset requests per hour"
    ),
    RateLimitCategory.SENSITIVE: RateLimitRule(
        limit=int(os.getenv("SENSITIVE_RATE_LIMIT", "30")),
        window_seconds=60,
        description="30 requests per minute for sensitive endpoints"
    ),
}


class InMemoryRateLimiter:
    """
    Thread-safe in-memory rate limiter using sliding window algorithm.
    """
    
    def __init__(self):
        self._events: Dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()
    
    def check(self, key: str, limit: int, window_seconds: int) -> Tuple[bool, int, int]:
        """
        Check if a request is allowed under rate limit.
        
        Args:
            key: Unique identifier for the rate limit bucket
            limit: Maximum number of requests allowed
            window_seconds: Time window in seconds
        
        Returns:
            Tuple of (allowed: bool, remaining: int, retry_after: int)
        """
        now = time.time()
        
        with self._lock:
            bucket = self._events[key]
            
            # Remove expired events
            while bucket and bucket[0] <= now - window_seconds:
                bucket.popleft()
            
            # Check if allowed
            allowed = len(bucket) < limit
            
            if allowed:
                bucket.append(now)
            
            # Calculate remaining and retry_after
            remaining = max(0, limit - len(bucket))
            retry_after = 0
            
            if bucket and not allowed:
                retry_after = max(1, int(window_seconds - (now - bucket[0])))
            
            return allowed, remaining, retry_after
    
    def get_current_count(self, key: str, window_seconds: int) -> int:
        """Get current request count for a key within window."""
        now = time.time()
        
        with self._lock:
            bucket = self._events[key]
            
            # Remove expired events
            while bucket and bucket[0] <= now - window_seconds:
                bucket.popleft()
            
            return len(bucket)
    
    def reset(self, key: str):
        """Reset rate limit for a specific key."""
        with self._lock:
            if key in self._events:
                del self._events[key]
    
    def clear_expired(self, max_age_seconds: int = 3600):
        """Clear expired entries older than max_age."""
        now = time.time()
        
        with self._lock:
            keys_to_remove = []
            for key, bucket in self._events.items():
                # Keep only events within the last max_age_seconds
                while bucket and bucket[0] <= now - max_age_seconds:
                    bucket.popleft()
                
                if not bucket:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self._events[key]


class RedisRateLimiter:
    """
    Redis-backed rate limiter for multi-instance deployments.
    Falls back gracefully by raising RuntimeError on connectivity issues.
    """

    def __init__(self, redis_url: str):
        try:
            import redis  # type: ignore
        except ImportError as exc:
            raise RuntimeError("redis package is required for Redis rate limiting") from exc

        self._client = redis.Redis.from_url(redis_url, decode_responses=True)
        self._check_script = self._client.register_script(
            """
            local key = KEYS[1]
            local now_ms = tonumber(ARGV[1])
            local cutoff_ms = tonumber(ARGV[2])
            local limit = tonumber(ARGV[3])
            local window_seconds = tonumber(ARGV[4])
            local member = ARGV[5]

            redis.call('ZREMRANGEBYSCORE', key, 0, cutoff_ms)
            local count = redis.call('ZCARD', key)

            if count < limit then
                redis.call('ZADD', key, now_ms, member)
                redis.call('EXPIRE', key, window_seconds + 60)
                return {1, limit - (count + 1), 0}
            end

            local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
            local retry_after = 1
            if oldest[2] then
                retry_after = math.max(1, math.floor((tonumber(oldest[2]) + (window_seconds * 1000) - now_ms) / 1000))
            end
            return {0, 0, retry_after}
            """
        )

    @staticmethod
    def _key(bucket_key: str) -> str:
        return f"jobbot:ratelimit:{bucket_key}"

    def check(self, key: str, limit: int, window_seconds: int) -> Tuple[bool, int, int]:
        now = time.time()
        now_ms = int(now * 1000)
        cutoff_ms = int((now - window_seconds) * 1000)
        redis_key = self._key(key)
        member = f"{now_ms}:{uuid4().hex}"
        result = self._check_script(
            keys=[redis_key],
            args=[now_ms, cutoff_ms, limit, window_seconds, member],
        )
        allowed = bool(int(result[0]))
        remaining = int(result[1])
        retry_after = int(result[2])
        return allowed, remaining, retry_after

    def get_current_count(self, key: str, window_seconds: int) -> int:
        now = time.time()
        cutoff_ms = int((now - window_seconds) * 1000)
        redis_key = self._key(key)
        pipe = self._client.pipeline()
        pipe.zremrangebyscore(redis_key, 0, cutoff_ms)
        pipe.zcard(redis_key)
        _, count = pipe.execute()
        return int(count or 0)

    def reset(self, key: str):
        self._client.delete(self._key(key))

    def clear_expired(self, max_age_seconds: int = 3600):
        # Redis key TTL handles expiration, explicit cleanup not required.
        return


class EndpointRateLimiter:
    """
    Enhanced rate limiter with per-endpoint rules and category-based limits.
    """
    
    def __init__(self, rules: Optional[Dict[RateLimitCategory, RateLimitRule]] = None):
        backend = (os.getenv("RATE_LIMIT_BACKEND", "memory") or "memory").lower()
        redis_url = os.getenv("REDIS_URL", "").strip()
        self._memory_limiter = InMemoryRateLimiter()
        self._redis_enabled = backend == "redis"
        self._fallback_warned = False
        if backend == "redis" and redis_url:
            try:
                self._limiter = RedisRateLimiter(redis_url)
                logger.info("Rate limit backend initialized: redis")
            except Exception:
                logger.warning(
                    "RATE_LIMIT_BACKEND=redis was requested, but Redis could not be initialized; falling back to memory"
                )
                self._limiter = self._memory_limiter
                self._redis_enabled = False
        else:
            if backend == "redis" and not redis_url:
                logger.warning(
                    "RATE_LIMIT_BACKEND=redis was requested, but REDIS_URL is empty; falling back to memory"
                )
            self._limiter = self._memory_limiter
            logger.info("Rate limit backend initialized: memory")
        self._rules = rules or DEFAULT_RULES.copy()
        self._endpoint_categories: Dict[str, RateLimitCategory] = {}
    
    def register_endpoint(self, path: str, category: RateLimitCategory):
        """
        Register an endpoint path to a rate limit category.
        
        Args:
            path: URL path pattern (e.g., "/auth/login")
            category: Rate limit category
        """
        self._endpoint_categories[path] = category
    
    def check_endpoint(
        self,
        path: str,
        identity: str,
        category: Optional[RateLimitCategory] = None
    ) -> Tuple[bool, int, int]:
        """
        Check rate limit for an endpoint.
        
        Args:
            path: URL path
            identity: User identifier (IP or user ID)
            category: Optional explicit category override
        
        Returns:
            Tuple of (allowed: bool, remaining: int, retry_after: int)
        """
        # Determine category
        if category is None:
            category = self._get_category_for_path(path)
        
        # Get default rule if no specific category
        if category is None or category not in self._rules:
            category = RateLimitCategory.API_GENERAL
        
        rule = self._rules[category]
        key = f"{category.value}:{identity}"

        try:
            return self._limiter.check(key, rule.limit, rule.window_seconds)
        except Exception as exc:
            if self._redis_enabled and not self._fallback_warned:
                logger.warning(
                    "Redis rate limiter failed at runtime; switching this process to in-memory fallback: %s",
                    exc,
                )
                self._fallback_warned = True
            self._redis_enabled = False
            self._limiter = self._memory_limiter
            return self._memory_limiter.check(key, rule.limit, rule.window_seconds)
    
    def _get_category_for_path(self, path: str) -> Optional[RateLimitCategory]:
        """Determine rate limit category based on path."""
        # Check exact matches first
        if path in self._endpoint_categories:
            return self._endpoint_categories[path]
        
        # Check path prefixes
        for pattern, category in self._endpoint_categories.items():
            if path.startswith(pattern):
                return category
        
        # Check special patterns
        if "/auth/login" in path or "/auth/token" in path:
            return RateLimitCategory.LOGIN
        if "/auth/register" in path:
            return RateLimitCategory.REGISTER
        if "/webhooks/" in path or "/subscriptions/webhook" in path:
            return RateLimitCategory.WEBHOOKS
        if "/auth/password-reset" in path or "/auth/forgot-password" in path:
            return RateLimitCategory.PASSWORD_RESET
        
        return None
    
    def get_rate_limit_headers(
        self,
        path: str,
        identity: str,
        allowed: bool,
        retry_after: int
    ) -> Dict[str, str]:
        """Generate rate limit headers for response."""
        category = self._get_category_for_path(path) or RateLimitCategory.API_GENERAL
        rule = self._rules.get(category, self._rules[RateLimitCategory.API_GENERAL])
        
        # Calculate remaining
        key = f"{category.value}:{identity}"
        try:
            current_count = self._limiter.get_current_count(key, rule.window_seconds)
        except Exception:
            current_count = self._memory_limiter.get_current_count(key, rule.window_seconds)
        remaining = max(0, rule.limit - current_count)
        reset_seconds = retry_after if not allowed else rule.window_seconds

        headers = {
            "X-RateLimit-Limit": str(rule.limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Window": str(rule.window_seconds),
            "X-RateLimit-Reset": str(int(time.time()) + max(1, reset_seconds)),
        }
        
        if not allowed:
            headers["Retry-After"] = str(retry_after)
        
        return headers
    
    def get_rule_description(self, category: RateLimitCategory) -> str:
        """Get human-readable description of a rate limit rule."""
        rule = self._rules.get(category)
        if rule:
            return rule.description or f"{rule.limit} per {rule.window_seconds}s"
        return "Unknown"


# Global rate limiter instance
rate_limiter = InMemoryRateLimiter()
endpoint_rate_limiter = EndpointRateLimiter()

# Legacy compatibility - module-level constants
LOGIN_LIMIT = DEFAULT_RULES[RateLimitCategory.LOGIN].limit
LOGIN_WINDOW_SECONDS = DEFAULT_RULES[RateLimitCategory.LOGIN].window_seconds
API_LIMIT = DEFAULT_RULES[RateLimitCategory.API_GENERAL].limit
API_WINDOW_SECONDS = DEFAULT_RULES[RateLimitCategory.API_GENERAL].window_seconds


def get_client_ip(request) -> str:
    """Extract client IP from request."""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check_rate_limit(
    path: str,
    method: str,
    identity: str,
    headers: Optional[Dict[str, str]] = None
) -> Tuple[bool, Dict[str, str]]:
    """
    Convenience function to check rate limit for a request.
    
    Args:
        path: Request path
        method: HTTP method
        identity: Client identity (IP or user ID)
        headers: Optional request headers
    
    Returns:
        Tuple of (allowed: bool, headers: dict)
    """
    allowed, remaining, retry_after = endpoint_rate_limiter.check_endpoint(
        path, identity
    )
    
    response_headers = endpoint_rate_limiter.get_rate_limit_headers(
        path, identity, allowed, retry_after
    )
    
    return allowed, response_headers


def enforce_rate_limit(
    path: str,
    method: str,
    identity: str,
    detail: str = "Demasiadas solicitudes. Intentá de nuevo en unos segundos.",
):
    """Raise 429 when the current request exceeds the configured bucket."""
    from fastapi import HTTPException

    allowed, response_headers = check_rate_limit(path, method, identity)
    if allowed:
        return response_headers

    raise HTTPException(
        status_code=429,
        detail=detail,
        headers=response_headers,
    )


def is_exempt_from_rate_limit(path: str, method: str) -> bool:
    """Check if a path is exempt from rate limiting."""
    exempt_paths = ["/health", "/ready", "/metrics", "/stats", "/docs", "/openapi.json"]
    return any(path.startswith(exempt) for exempt in exempt_paths)


# Register default endpoints
endpoint_rate_limiter.register_endpoint("/auth/token", RateLimitCategory.LOGIN)
endpoint_rate_limiter.register_endpoint("/auth/login", RateLimitCategory.LOGIN)
endpoint_rate_limiter.register_endpoint("/auth/register", RateLimitCategory.REGISTER)
endpoint_rate_limiter.register_endpoint("/auth/web-login-link", RateLimitCategory.LOGIN)
endpoint_rate_limiter.register_endpoint("/auth/telegram", RateLimitCategory.TELEGRAM)
endpoint_rate_limiter.register_endpoint("/auth/telegram/init", RateLimitCategory.TELEGRAM)
endpoint_rate_limiter.register_endpoint("/auth/telegram/code", RateLimitCategory.TELEGRAM)
endpoint_rate_limiter.register_endpoint("/auth/telegram/web-login-link", RateLimitCategory.TELEGRAM)
endpoint_rate_limiter.register_endpoint("/auth/telegram/link-code", RateLimitCategory.TELEGRAM)
endpoint_rate_limiter.register_endpoint("/webhooks", RateLimitCategory.WEBHOOKS)
endpoint_rate_limiter.register_endpoint("/subscriptions/webhook", RateLimitCategory.WEBHOOKS)
endpoint_rate_limiter.register_endpoint("/jobs/search", RateLimitCategory.SEARCH)
endpoint_rate_limiter.register_endpoint("/jobs/recommended", RateLimitCategory.SEARCH)
endpoint_rate_limiter.register_endpoint("/jobs/dashboard-preview", RateLimitCategory.SEARCH)
endpoint_rate_limiter.register_endpoint("/jobs/track", RateLimitCategory.SEARCH)
endpoint_rate_limiter.register_endpoint("/jobs/applications", RateLimitCategory.SEARCH)
endpoint_rate_limiter.register_endpoint("/cv/upload", RateLimitCategory.CV)
endpoint_rate_limiter.register_endpoint("/cv/analyze", RateLimitCategory.CV)
endpoint_rate_limiter.register_endpoint("/cv/proposal", RateLimitCategory.CV)
endpoint_rate_limiter.register_endpoint("/cv/mock-interview", RateLimitCategory.CV)
endpoint_rate_limiter.register_endpoint("/cv/tips", RateLimitCategory.CV)
endpoint_rate_limiter.register_endpoint("/users/dashboard", RateLimitCategory.DASHBOARD)
endpoint_rate_limiter.register_endpoint("/users/preferences", RateLimitCategory.DASHBOARD)
endpoint_rate_limiter.register_endpoint("/users/usage", RateLimitCategory.DASHBOARD)
endpoint_rate_limiter.register_endpoint("/users/me", RateLimitCategory.DASHBOARD)

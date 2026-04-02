"""
Core security, caching, and reliability utilities for JobBot API.
"""

from .security import (
    TokenBlacklist,
    RefreshTokenManager,
    create_access_token,
    create_refresh_token,
    decode_token,
    validate_jwt_secret,
    verify_telegram_auth,
    generate_token_id,
    hash_token,
    get_token_blacklist,
    get_refresh_token_manager,
)

from .cache import (
    cache,
    CacheManager,
    job_search_cache,
    user_dashboard_cache,
    user_profile_cache,
    job_details_cache,
    job_search_key,
    user_dashboard_key,
    user_profile_key,
    job_details_key,
)

from .reliability import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    CircuitBreakerOpenError,
    get_circuit_breaker,
    get_all_circuit_breakers,
    telegram_circuit,
    stripe_circuit,
    scraping_circuit,
    retry_with_backoff,
    retry,
    RetryConfig,
    DeadLetterQueue,
    dlq,
    GracefulShutdown,
    graceful_shutdown,
)

__all__ = [
    # Security
    "TokenBlacklist",
    "RefreshTokenManager",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "validate_jwt_secret",
    "verify_telegram_auth",
    "generate_token_id",
    "hash_token",
    "get_token_blacklist",
    "get_refresh_token_manager",
    # Cache
    "cache",
    "CacheManager",
    "job_search_cache",
    "user_dashboard_cache",
    "user_profile_cache",
    "job_details_cache",
    "job_search_key",
    "user_dashboard_key",
    "user_profile_key",
    "job_details_key",
    # Reliability
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitState",
    "CircuitBreakerOpenError",
    "get_circuit_breaker",
    "get_all_circuit_breakers",
    "telegram_circuit",
    "stripe_circuit",
    "scraping_circuit",
    "retry_with_backoff",
    "retry",
    "RetryConfig",
    "DeadLetterQueue",
    "dlq",
    "GracefulShutdown",
    "graceful_shutdown",
]

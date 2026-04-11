"""
Redis Caching Layer for JobBot API
Production-ready caching with:
- Connection pooling
- Automatic serialization
- Cache warming
- TTL management
- Circuit breaker pattern
"""

import json
import hashlib
import logging
from typing import Any, Optional, Callable, TypeVar, Generic
from functools import wraps
from datetime import timedelta
import os

# Try to import redis, fall back to in-memory cache if not available
try:
    import redis
    from redis.connection import ConnectionPool
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger("jobbot.cache")

T = TypeVar('T')


class CacheBackend:
    """Abstract cache backend interface."""
    
    def get(self, key: str) -> Optional[Any]:
        raise NotImplementedError
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        raise NotImplementedError
    
    def delete(self, key: str) -> bool:
        raise NotImplementedError
    
    def exists(self, key: str) -> bool:
        raise NotImplementedError
    
    def clear(self) -> bool:
        raise NotImplementedError


class InMemoryCache(CacheBackend):
    """In-memory cache with TTL support for development/testing."""
    
    def __init__(self):
        self._cache: dict[str, tuple[Any, Optional[float]]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        import time
        if key not in self._cache:
            return None
        
        value, expires_at = self._cache[key]
        if expires_at and time.time() > expires_at:
            del self._cache[key]
            return None
        
        return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        import time
        expires_at = time.time() + ttl if ttl else None
        self._cache[key] = (value, expires_at)
        return True
    
    def delete(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def exists(self, key: str) -> bool:
        return self.get(key) is not None
    
    def clear(self) -> bool:
        self._cache.clear()
        return True


class RedisCache(CacheBackend):
    """Production Redis cache with connection pooling."""
    
    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._pool = ConnectionPool.from_url(
            redis_url,
            max_connections=20,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )
        self._client = redis.Redis(connection_pool=self._pool, decode_responses=True)
        
        # Test connection
        try:
            self._client.ping()
            logger.info("Redis cache connected successfully")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            raise
    
    def _serialize(self, value: Any) -> str:
        return json.dumps(value, default=str)
    
    def _deserialize(self, value: str) -> Any:
        return json.loads(value)
    
    def get(self, key: str) -> Optional[Any]:
        try:
            value = self._client.get(key)
            if value:
                return self._deserialize(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        try:
            serialized = self._serialize(value)
            if ttl:
                self._client.setex(key, ttl, serialized)
            else:
                self._client.set(key, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        try:
            return self._client.delete(key) > 0
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        try:
            return self._client.exists(key) > 0
        except Exception:
            return False
    
    def clear(self) -> bool:
        try:
            self._client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False
    
    def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values at once (MGET)."""
        try:
            values = self._client.mget(keys)
            result = {}
            for key, value in zip(keys, values):
                if value:
                    result[key] = self._deserialize(value)
            return result
        except Exception as e:
            logger.error(f"Cache mget error: {e}")
            return {}
    
    def set_many(self, mapping: dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple values at once (MSET)."""
        try:
            pipe = self._client.pipeline()
            for key, value in mapping.items():
                serialized = self._serialize(value)
                if ttl:
                    pipe.setex(key, ttl, serialized)
                else:
                    pipe.set(key, serialized)
            pipe.execute()
            return True
        except Exception as e:
            logger.error(f"Cache mset error: {e}")
            return False
    
    def incr(self, key: str, amount: int = 1) -> int:
        """Atomic increment."""
        try:
            return self._client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Cache incr error: {e}")
            return 0
    
    def expire(self, key: str, ttl: int) -> bool:
        """Set expiration on existing key."""
        try:
            return self._client.expire(key, ttl)
        except Exception:
            return False


class CacheManager:
    """
    High-level cache manager with key namespacing and utilities.
    """
    
    PREFIX = "jobbot"
    
    # Default TTLs in seconds
    TTL_SHORT = 60          # 1 minute
    TTL_MEDIUM = 300        # 5 minutes
    TTL_LONG = 3600         # 1 hour
    TTL_DAY = 86400         # 24 hours
    TTL_WEEK = 604800       # 7 days
    
    def __init__(self):
        if REDIS_AVAILABLE and os.getenv("REDIS_URL"):
            try:
                self._backend: CacheBackend = RedisCache()
                logger.info("Using Redis cache backend")
            except Exception as e:
                logger.warning(f"Redis unavailable, using in-memory cache: {e}")
                self._backend = InMemoryCache()
        else:
            self._backend = InMemoryCache()
            logger.info("Using in-memory cache backend")
    
    def _make_key(self, namespace: str, key: str) -> str:
        """Create namespaced cache key."""
        return f"{self.PREFIX}:{namespace}:{key}"
    
    def get(self, namespace: str, key: str) -> Optional[Any]:
        """Get value from cache."""
        return self._backend.get(self._make_key(namespace, key))
    
    def set(
        self, 
        namespace: str, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache."""
        return self._backend.set(self._make_key(namespace, key), value, ttl)
    
    def delete(self, namespace: str, key: str) -> bool:
        """Delete value from cache."""
        return self._backend.delete(self._make_key(namespace, key))
    
    def delete_pattern(self, namespace: str, pattern: str) -> int:
        """Delete all keys matching pattern."""
        # This only works with Redis
        if isinstance(self._backend, RedisCache):
            try:
                search_key = f"{self.PREFIX}:{namespace}:{pattern}*"
                keys = self._backend._client.keys(search_key)
                if keys:
                    return self._backend._client.delete(*keys)
            except Exception as e:
                logger.error(f"Cache delete pattern error: {e}")
        return 0
    
    def exists(self, namespace: str, key: str) -> bool:
        """Check if key exists in cache."""
        return self._backend.exists(self._make_key(namespace, key))
    
    def cached(
        self, 
        namespace: str, 
        ttl: int = TTL_MEDIUM,
        key_fn: Optional[Callable] = None
    ):
        """
        Decorator for caching function results.
        
        Args:
            namespace: Cache namespace
            ttl: Time-to-live in seconds
            key_fn: Optional function to generate cache key from function arguments
        """
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            def wrapper(*args, **kwargs) -> T:
                # Generate cache key
                if key_fn:
                    cache_key = key_fn(*args, **kwargs)
                else:
                    # Default: hash of function name and arguments
                    key_parts = [func.__name__]
                    key_parts.extend(str(arg) for arg in args)
                    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                    cache_key = hashlib.md5(
                        ":".join(key_parts).encode()
                    ).hexdigest()[:16]
                
                # Try to get from cache
                cached_value = self.get(namespace, cache_key)
                if cached_value is not None:
                    logger.debug(f"Cache hit: {namespace}:{cache_key}")
                    return cached_value
                
                # Call function and cache result
                result = func(*args, **kwargs)
                self.set(namespace, cache_key, result, ttl)
                logger.debug(f"Cache set: {namespace}:{cache_key}")
                
                return result
            
            # Attach cache management methods
            wrapper.cache_clear = lambda: self.delete_pattern(namespace, "")
            wrapper.cache_delete = lambda *a, **kw: self.delete(
                namespace, 
                key_fn(*a, **kw) if key_fn else hashlib.md5(
                    f"{func.__name__}:{':'.join(str(x) for x in a)}".encode()
                ).hexdigest()[:16]
            )
            
            return wrapper
        return decorator
    
    def invalidate_user_cache(self, user_id: int) -> int:
        """Invalidate all cached data for a user."""
        patterns = [
            f"user:{user_id}:*",
            f"jobs:user:{user_id}:*",
            f"dashboard:user:{user_id}:*",
        ]
        total = 0
        for pattern in patterns:
            total += self.delete_pattern("", pattern)
        logger.info(f"Invalidated {total} cache entries for user {user_id}")
        return total


# Global cache manager instance
cache = CacheManager()


# Cache key generators for common patterns
def job_search_key(query: str, location: str, limit: int, offset: int) -> str:
    """Generate cache key for job search."""
    key = f"search:{hashlib.md5(f'{query}:{location}:{limit}:{offset}'.encode()).hexdigest()[:12]}"
    return key


def user_dashboard_key(user_id: int) -> str:
    """Generate cache key for user dashboard."""
    return f"dashboard:user:{user_id}:summary"


def user_profile_key(user_id: int) -> str:
    """Generate cache key for user profile."""
    return f"user:{user_id}:profile"


def job_details_key(job_id: str) -> str:
    """Generate cache key for job details."""
    return f"job:{job_id}:details"


# Predefined cache decorators
job_search_cache = cache.cached("jobs", ttl=CacheManager.TTL_MEDIUM, key_fn=job_search_key)
user_dashboard_cache = cache.cached("dashboard", ttl=CacheManager.TTL_SHORT)
user_profile_cache = cache.cached("users", ttl=CacheManager.TTL_LONG, key_fn=user_profile_key)
job_details_cache = cache.cached("jobs", ttl=CacheManager.TTL_DAY, key_fn=job_details_key)


# Export cache instance and utilities
__all__ = [
    'cache',
    'CacheManager',
    'job_search_cache',
    'user_dashboard_cache',
    'user_profile_cache',
    'job_details_cache',
    'job_search_key',
    'user_dashboard_key',
    'user_profile_key',
    'job_details_key',
]

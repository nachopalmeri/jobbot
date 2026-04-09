"""
Reliability Patterns for JobBot API
Circuit Breaker, Retry Logic, Dead Letter Queue, Graceful Shutdown
"""

import asyncio
import logging
import time
from typing import Any, Callable, TypeVar, Optional, List
from enum import Enum
from functools import wraps
from dataclasses import dataclass
from datetime import datetime, timedelta
import os
import signal
import json

logger = logging.getLogger("jobbot.reliability")

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5
    success_threshold: int = 3
    timeout_seconds: float = 30.0
    reset_timeout_seconds: float = 60.0
    half_open_max_calls: int = 3


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.
    Prevents cascade failures when external services are down.
    """
    
    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.half_open_calls = 0
        self._lock = asyncio.Lock()
    
    async def call(self, operation: Callable[..., T], *args, **kwargs) -> T:
        """Execute operation with circuit breaker protection."""
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_calls = 0
                    logger.info(f"Circuit breaker '{self.name}' entering HALF_OPEN state")
                else:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.name}' is OPEN"
                    )
            
            if self.state == CircuitState.HALF_OPEN:
                if self.half_open_calls >= self.config.half_open_max_calls:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.name}' HALF_OPEN limit reached"
                    )
                self.half_open_calls += 1
        
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                operation(*args, **kwargs),
                timeout=self.config.timeout_seconds
            )
            await self._on_success()
            return result
        except asyncio.TimeoutError:
            await self._on_failure()
            raise TimeoutError(
                f"Operation '{self.name}' timed out after {self.config.timeout_seconds}s"
            )
        except Exception as e:
            await self._on_failure()
            raise
    
    async def _on_success(self):
        """Handle successful operation."""
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self._close_circuit()
            else:
                self.failure_count = 0
    
    async def _on_failure(self):
        """Handle failed operation."""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                self._open_circuit()
            elif self.failure_count >= self.config.failure_threshold:
                self._open_circuit()
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit."""
        if self.last_failure_time is None:
            return True
        elapsed = time.time() - self.last_failure_time
        return elapsed >= self.config.reset_timeout_seconds
    
    def _open_circuit(self):
        """Open the circuit."""
        if self.state != CircuitState.OPEN:
            logger.warning(
                f"Circuit breaker '{self.name}' OPENED after {self.failure_count} failures"
            )
        self.state = CircuitState.OPEN
        self.success_count = 0
    
    def _close_circuit(self):
        """Close the circuit."""
        logger.info(
            f"Circuit breaker '{self.name}' CLOSED after {self.success_count} successes"
        )
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
    
    def get_state(self) -> CircuitState:
        """Get current circuit state."""
        return self.state
    
    def get_metrics(self) -> dict:
        """Get circuit breaker metrics."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
        }


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


# Global circuit breaker registry
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
    """Get or create a circuit breaker."""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name, config)
    return _circuit_breakers[name]


def get_all_circuit_breakers() -> dict[str, CircuitBreaker]:
    """Get all registered circuit breakers."""
    return _circuit_breakers.copy()


@dataclass
class RetryConfig:
    """Configuration for retry logic."""
    max_retries: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    exponential_base: float = 2.0
    retryable_exceptions: tuple = (Exception,)
    on_retry: Optional[Callable[[int, Exception], None]] = None


async def retry_with_backoff(
    operation: Callable[..., T],
    config: Optional[RetryConfig] = None,
    *args,
    **kwargs
) -> T:
    """
    Execute operation with exponential backoff retry logic.
    
    Args:
        operation: Async function to execute
        config: Retry configuration
        *args, **kwargs: Arguments to pass to operation
    
    Returns:
        Result of operation
    
    Raises:
        Last exception if all retries failed
    """
    cfg = config or RetryConfig()
    last_exception: Optional[Exception] = None
    
    for attempt in range(cfg.max_retries + 1):
        try:
            return await operation(*args, **kwargs)
        except cfg.retryable_exceptions as e:
            last_exception = e
            
            if attempt == cfg.max_retries:
                logger.error(
                    f"Operation failed after {cfg.max_retries} retries: {e}"
                )
                raise
            
            # Calculate delay with exponential backoff and jitter
            delay = min(
                cfg.base_delay_seconds * (cfg.exponential_base ** attempt),
                cfg.max_delay_seconds
            )
            # Add jitter (±25%)
            jitter = delay * 0.25 * (2 * (time.time() % 1) - 1)
            delay += jitter
            
            logger.warning(
                f"Attempt {attempt + 1}/{cfg.max_retries + 1} failed: {e}. "
                f"Retrying in {delay:.2f}s..."
            )
            
            if cfg.on_retry:
                cfg.on_retry(attempt + 1, e)
            
            await asyncio.sleep(delay)
    
    if last_exception:
        raise last_exception
    
    raise RuntimeError("Unexpected state in retry logic")


def retry(**retry_kwargs):
    """Decorator for adding retry logic to async functions."""
    config = RetryConfig(**retry_kwargs)
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await retry_with_backoff(func, config, *args, **kwargs)
        return wrapper
    return decorator


# Predefined circuit breakers for external services
telegram_circuit = get_circuit_breaker(
    "telegram",
    CircuitBreakerConfig(
        failure_threshold=3,
        reset_timeout_seconds=30.0
    )
)

stripe_circuit = get_circuit_breaker(
    "stripe",
    CircuitBreakerConfig(
        failure_threshold=5,
        reset_timeout_seconds=60.0
    )
)

scraping_circuit = get_circuit_breaker(
    "scraping",
    CircuitBreakerConfig(
        failure_threshold=10,
        reset_timeout_seconds=120.0,
        timeout_seconds=60.0
    )
)


class DeadLetterQueue:
    """
    Dead Letter Queue for failed webhooks and async tasks.
    Stores failed operations for later retry.
    """
    
    def __init__(self, database=None):
        self.db = database
        self._memory_queue: List[dict] = []
    
    async def enqueue(
        self,
        operation_type: str,
        payload: dict,
        error: str,
        max_retries: int = 3
    ) -> bool:
        """
        Add failed operation to DLQ.
        
        Args:
            operation_type: Type of operation (webhook, notification, etc.)
            payload: Original operation payload
            error: Error message
            max_retries: Maximum retry attempts
        
        Returns:
            True if successfully queued
        """
        entry = {
            "operation_type": operation_type,
            "payload": json.dumps(payload),
            "error": error,
            "retry_count": 0,
            "max_retries": max_retries,
            "created_at": datetime.utcnow().isoformat(),
            "next_retry_at": (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
        }
        
        if self.db:
            try:
                self.db.create_dlq_entry(**entry)
                logger.info(f"Added {operation_type} to DLQ")
                return True
            except Exception as e:
                logger.error(f"Failed to add to DLQ: {e}")
        
        # Fallback to memory queue
        self._memory_queue.append(entry)
        return True
    
    async def process_dlq(self, processor: Callable[[str, dict], bool]) -> int:
        """
        Process entries in the dead letter queue.
        
        Args:
            processor: Function to process recovered operations
        
        Returns:
            Number of successfully processed entries
        """
        processed = 0
        
        if self.db:
            try:
                entries = self.db.get_dlq_entries_for_retry()
                for entry in entries:
                    try:
                        payload = json.loads(entry["payload"])
                        success = processor(entry["operation_type"], payload)
                        
                        if success:
                            self.db.mark_dlq_entry_processed(entry["id"])
                            processed += 1
                        else:
                            self._increment_retry(entry)
                    except Exception as e:
                        logger.error(f"DLQ processing error: {e}")
                        self._increment_retry(entry)
            except Exception as e:
                logger.error(f"Failed to fetch DLQ entries: {e}")
        
        # Process memory queue
        for entry in list(self._memory_queue):
            if datetime.fromisoformat(entry["next_retry_at"]) <= datetime.utcnow():
                try:
                    payload = json.loads(entry["payload"])
                    success = processor(entry["operation_type"], payload)
                    
                    if success:
                        self._memory_queue.remove(entry)
                        processed += 1
                    else:
                        self._increment_retry(entry)
                except Exception as e:
                    logger.error(f"Memory DLQ processing error: {e}")
                    self._increment_retry(entry)
        
        return processed
    
    def _increment_retry(self, entry: dict):
        """Increment retry count and schedule next attempt."""
        entry["retry_count"] += 1
        if entry["retry_count"] >= entry["max_retries"]:
            entry["failed_permanently"] = True
            logger.error(
                f"DLQ entry {entry.get('id', 'memory')} failed permanently"
            )
        else:
            # Exponential backoff: 5min, 15min, 45min
            delay_minutes = 5 * (3 ** (entry["retry_count"] - 1))
            entry["next_retry_at"] = (
                datetime.utcnow() + timedelta(minutes=delay_minutes)
            ).isoformat()


class GracefulShutdown:
    """
    Handles graceful shutdown of the application.
    Ensures all ongoing requests are completed before shutting down.
    """
    
    def __init__(self, timeout_seconds: float = 30.0):
        self.timeout_seconds = timeout_seconds
        self._shutdown_event = asyncio.Event()
        self._active_requests = 0
        self._shutdown_handlers: List[Callable] = []
    
    def register_handler(self, handler: Callable):
        """Register a callback to run during shutdown."""
        self._shutdown_handlers.append(handler)
    
    async def request_context(self):
        """Context manager for tracking active requests."""
        self._active_requests += 1
        try:
            yield
        finally:
            self._active_requests -= 1
    
    async def shutdown(self):
        """Initiate graceful shutdown."""
        logger.info("Initiating graceful shutdown...")
        self._shutdown_event.set()
        
        # Wait for active requests to complete
        start_time = time.time()
        while self._active_requests > 0:
            elapsed = time.time() - start_time
            if elapsed > self.timeout_seconds:
                logger.warning(
                    f"Force shutdown after {self.timeout_seconds}s, "
                    f"{self._active_requests} requests still active"
                )
                break
            logger.info(
                f"Waiting for {self._active_requests} active requests..."
            )
            await asyncio.sleep(0.5)
        
        # Run shutdown handlers
        for handler in self._shutdown_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler()
                else:
                    handler()
            except Exception as e:
                logger.error(f"Shutdown handler error: {e}")
        
        logger.info("Graceful shutdown complete")
    
    def setup_signal_handlers(self):
        """Setup Unix signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)


# Global instances
dlq = DeadLetterQueue()
graceful_shutdown = GracefulShutdown()


# Export public API
__all__ = [
    'CircuitBreaker',
    'CircuitBreakerConfig',
    'CircuitState',
    'CircuitBreakerOpenError',
    'get_circuit_breaker',
    'get_all_circuit_breakers',
    'telegram_circuit',
    'stripe_circuit',
    'scraping_circuit',
    'retry_with_backoff',
    'retry',
    'RetryConfig',
    'DeadLetterQueue',
    'dlq',
    'GracefulShutdown',
    'graceful_shutdown',
]

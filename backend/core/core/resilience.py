"""
Resilience patterns for reliable service calls.
Includes circuit breaker pattern and exponential backoff retry logic.
"""
import logging
import time
from functools import wraps
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """States for the circuit breaker pattern."""
    CLOSED = "closed"          # Normal operation
    OPEN = "open"              # Rejecting requests
    HALF_OPEN = "half_open"   # Testing if service recovered


class CircuitBreaker:
    """
    Circuit Breaker pattern implementation.
    Prevents cascading failures by stopping requests to failing services.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service is failing, requests are rejected immediately
    - HALF_OPEN: Service might have recovered, test with limited requests
    """
    
    def __init__(
        self,
        failure_threshold=5,
        recovery_timeout=60,
        expected_exception=Exception,
        name="CircuitBreaker"
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before trying half-open (default: 60s)
            expected_exception: Exception type to catch
            name: Name for logging
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name
        
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = None
    
    def call(self, func, *args, **kwargs):
        """
        Execute function through circuit breaker.
        
        Raises:
            CircuitBreakerOpen: If circuit is open
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info(f"[{self.name}] Circuit breaker entering HALF_OPEN state")
            else:
                raise CircuitBreakerOpen(f"Circuit breaker {self.name} is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as exc:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self._reset()
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(
                f"[{self.name}] Circuit breaker opened after {self.failure_count} failures"
            )
    
    def _should_attempt_reset(self):
        """Check if enough time has passed to try recovery."""
        if self.last_failure_time is None:
            return True
        
        return (
            datetime.now() - self.last_failure_time
            >= timedelta(seconds=self.recovery_timeout)
        )
    
    def _reset(self):
        """Reset circuit breaker to closed state."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        logger.info(f"[{self.name}] Circuit breaker reset to CLOSED state")


class CircuitBreakerOpen(Exception):
    """Exception raised when circuit breaker is open."""
    pass


def circuit_breaker(
    failure_threshold=5,
    recovery_timeout=60,
    expected_exception=Exception,
    name=None
):
    """
    Decorator for circuit breaker pattern.
    
    Usage:
        @circuit_breaker(failure_threshold=5, recovery_timeout=60)
        def call_external_api(url):
            return requests.get(url).json()
    
    Args:
        failure_threshold: Failures before opening circuit
        recovery_timeout: Seconds to wait before attempting recovery
        expected_exception: Exception type to catch
        name: Name for logging (defaults to function name)
    """
    def decorator(func):
        cb = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception,
            name=name or func.__name__
        )
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return cb.call(func, *args, **kwargs)
        
        wrapper.circuit_breaker = cb
        return wrapper
    
    return decorator


def retry_with_backoff(
    max_retries=3,
    base_delay=1,
    max_delay=60,
    exponential_base=2,
    retryable_exceptions=(Exception,)
):
    """
    Decorator for retry logic with exponential backoff.
    
    Usage:
        @retry_with_backoff(max_retries=3, base_delay=1)
        def risky_operation():
            return requests.get('http://api.example.com')
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds (default: 1s)
        max_delay: Maximum delay between retries (default: 60s)
        exponential_base: Base for exponential calculation (default: 2)
        retryable_exceptions: Tuple of exceptions to retry on
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as exc:
                    last_exception = exc
                    
                    if attempt < max_retries:
                        # Calculate delay with exponential backoff
                        delay = min(
                            base_delay * (exponential_base ** attempt),
                            max_delay
                        )
                        
                        logger.warning(
                            f"[{func.__name__}] Attempt {attempt + 1} failed: {str(exc)}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"[{func.__name__}] All {max_retries + 1} attempts failed. "
                            f"Last error: {str(exc)}"
                        )
            
            raise last_exception
        
        return wrapper
    
    return decorator


def retry_async_with_backoff(max_retries=3, base_delay=2):
    """
    Decorator for Celery task retry logic with exponential backoff.
    Designed for use with Celery's retry mechanism.
    
    Usage:
        @shared_task(bind=True, max_retries=3)
        @retry_async_with_backoff(max_retries=3)
        def my_async_task(self, data):
            try:
                process(data)
            except Exception as exc:
                raise self.retry(exc=exc, countdown=2 ** self.request.retries)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        wrapper.max_retries = max_retries
        wrapper.base_delay = base_delay
        return wrapper
    
    return decorator

"""Enhanced error handling utilities"""

import time
import functools
from typing import Callable, TypeVar, Any, Type, Tuple
from .exceptions import RetryableError
from .interfaces import Logger

T = TypeVar("T")


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    backoff_factor: float = 2.0,
    retryable_exceptions: Tuple[Type[Exception], ...] = (RetryableError,),
):
    """Decorator for retrying operations with exponential backoff"""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e

                    if attempt == max_attempts - 1:
                        break

                    # Calculate delay
                    if isinstance(e, RetryableError):
                        delay = e.retry_after
                    else:
                        delay = base_delay * (backoff_factor**attempt)

                    time.sleep(delay)

            # Re-raise the last exception if all retries failed
            raise last_exception

        return wrapper

    return decorator


def safe_execute(
    operation: Callable[[], T],
    logger: Logger,
    operation_name: str = "operation",
    default_value: T = None,
    reraise: bool = False,
) -> T:
    """Safely execute an operation with logging"""
    try:
        logger.debug(f"Starting {operation_name}")
        result = operation()
        logger.debug(f"Completed {operation_name}")
        return result
    except Exception as e:
        logger.error(f"Error in {operation_name}: {e}")
        if reraise:
            raise
        return default_value


class CircuitBreaker:
    """Simple circuit breaker pattern implementation"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        logger: Logger = None,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._logger = logger
        self._failure_count = 0
        self._last_failure_time = None
        self._state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def call(self, func: Callable[[], T]) -> T:
        """Execute function through circuit breaker"""
        if self._state == "OPEN":
            if self._should_attempt_reset():
                self._state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func()
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(e)
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        return (
            self._last_failure_time is not None
            and time.time() - self._last_failure_time >= self.recovery_timeout
        )

    def _on_success(self):
        """Handle successful operation"""
        self._failure_count = 0
        self._state = "CLOSED"
        if self._logger:
            self._logger.debug("Circuit breaker: Operation successful")

    def _on_failure(self, exception: Exception):
        """Handle failed operation"""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._failure_count >= self.failure_threshold:
            self._state = "OPEN"
            if self._logger:
                self._logger.warning(
                    f"Circuit breaker opened after {self._failure_count} failures"
                )

        if self._logger:
            self._logger.error(f"Circuit breaker: Operation failed - {exception}")


def validate_config(config: Any, required_fields: list[str]) -> None:
    """Validate that configuration has all required fields"""
    from .exceptions import ConfigurationError

    missing_fields = []
    for field in required_fields:
        if not hasattr(config, field) or getattr(config, field) in [
            None,
            "",
            "MISSING_ID",
            "MISSING_SECRET",
            "MISSING_REDIRECT",
            "MISSING_AGENT",
            "MISSING_QUEUE_URL",
        ]:
            missing_fields.append(field)

    if missing_fields:
        raise ConfigurationError(
            f"Missing or invalid configuration fields: {', '.join(missing_fields)}"
        )

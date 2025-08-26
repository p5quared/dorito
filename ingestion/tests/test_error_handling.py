"""Tests for error handling and resilience features"""

import pytest
import time
from unittest.mock import Mock, patch

from shared.error_handling import (
    with_retry,
    safe_execute,
    CircuitBreaker,
    validate_config,
)
from shared.exceptions import RetryableError, RateLimitError, ConfigurationError


class TestRetryDecorator:
    """Test retry decorator functionality"""

    def test_retry_succeeds_on_first_attempt(self):
        """Test that retry decorator passes through successful operations"""
        mock_func = Mock(return_value="success")
        decorated = with_retry(max_attempts=3)(mock_func)

        result = decorated("arg1", kwarg1="value1")

        assert result == "success"
        mock_func.assert_called_once_with("arg1", kwarg1="value1")

    def test_retry_eventually_succeeds(self):
        """Test that retry decorator retries until success"""
        mock_func = Mock(
            side_effect=[RetryableError("fail"), RetryableError("fail"), "success"]
        )

        with patch("time.sleep") as mock_sleep:
            decorated = with_retry(max_attempts=3, base_delay=0.1)(mock_func)
            result = decorated()

        assert result == "success"
        assert mock_func.call_count == 3
        assert mock_sleep.call_count == 2

    def test_retry_exhausts_attempts(self):
        """Test that retry decorator fails after max attempts"""
        mock_func = Mock(side_effect=RetryableError("persistent failure"))

        with patch("time.sleep"):
            decorated = with_retry(max_attempts=2, base_delay=0.1)(mock_func)

            with pytest.raises(RetryableError, match="persistent failure"):
                decorated()

        assert mock_func.call_count == 2

    def test_retry_respects_custom_delay(self):
        """Test that retry decorator uses custom delay from RetryableError"""
        custom_error = RateLimitError("rate limited", retry_after=5)
        mock_func = Mock(side_effect=[custom_error, "success"])

        with patch("time.sleep") as mock_sleep:
            decorated = with_retry(max_attempts=2)(mock_func)
            result = decorated()

        assert result == "success"
        mock_sleep.assert_called_once_with(5)  # Should use custom retry_after

    def test_retry_non_retryable_exception(self):
        """Test that non-retryable exceptions are not retried"""
        mock_func = Mock(side_effect=ValueError("not retryable"))
        decorated = with_retry(max_attempts=3)(mock_func)

        with pytest.raises(ValueError, match="not retryable"):
            decorated()

        mock_func.assert_called_once()  # Should not retry


class TestSafeExecute:
    """Test safe execute utility function"""

    def test_safe_execute_success(self):
        """Test safe execute with successful operation"""
        mock_logger = Mock()
        operation = Mock(return_value="result")

        result = safe_execute(operation, mock_logger, operation_name="test_op")

        assert result == "result"
        mock_logger.debug.assert_any_call("Starting test_op")
        mock_logger.debug.assert_any_call("Completed test_op")
        mock_logger.error.assert_not_called()

    def test_safe_execute_with_exception_no_reraise(self):
        """Test safe execute with exception (no reraise)"""
        mock_logger = Mock()
        operation = Mock(side_effect=Exception("test error"))

        result = safe_execute(
            operation,
            mock_logger,
            operation_name="failing_op",
            default_value="default",
            reraise=False,
        )

        assert result == "default"
        mock_logger.error.assert_called_once()
        assert "failing_op" in mock_logger.error.call_args[0][0]
        assert "test error" in mock_logger.error.call_args[0][0]

    def test_safe_execute_with_exception_reraise(self):
        """Test safe execute with exception (reraise)"""
        mock_logger = Mock()
        operation = Mock(side_effect=ValueError("test error"))

        with pytest.raises(ValueError, match="test error"):
            safe_execute(
                operation, mock_logger, operation_name="failing_op", reraise=True
            )

        mock_logger.error.assert_called_once()


class TestCircuitBreaker:
    """Test circuit breaker pattern implementation"""

    def test_circuit_breaker_normal_operation(self):
        """Test circuit breaker in normal (closed) state"""
        mock_logger = Mock()
        cb = CircuitBreaker(failure_threshold=3, logger=mock_logger)
        mock_func = Mock(return_value="success")

        result = cb.call(mock_func)

        assert result == "success"
        assert cb._state == "CLOSED"
        assert cb._failure_count == 0

    def test_circuit_breaker_opens_after_failures(self):
        """Test circuit breaker opens after reaching failure threshold"""
        mock_logger = Mock()
        cb = CircuitBreaker(failure_threshold=2, logger=mock_logger)
        mock_func = Mock(side_effect=Exception("error"))

        # First failure
        with pytest.raises(Exception):
            cb.call(mock_func)
        assert cb._state == "CLOSED"
        assert cb._failure_count == 1

        # Second failure - should open circuit
        with pytest.raises(Exception):
            cb.call(mock_func)
        assert cb._state == "OPEN"
        assert cb._failure_count == 2

        mock_logger.warning.assert_called_once()
        assert "Circuit breaker opened" in mock_logger.warning.call_args[0][0]

    def test_circuit_breaker_blocks_when_open(self):
        """Test circuit breaker blocks calls when open"""
        cb = CircuitBreaker(failure_threshold=1)
        mock_func = Mock(side_effect=Exception("error"))

        # Trigger circuit to open
        with pytest.raises(Exception):
            cb.call(mock_func)

        # Next call should be blocked
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            cb.call(mock_func)

        # Function should not have been called the second time
        assert mock_func.call_count == 1

    def test_circuit_breaker_half_open_recovery(self):
        """Test circuit breaker recovery through half-open state"""
        mock_logger = Mock()
        cb = CircuitBreaker(
            failure_threshold=1, recovery_timeout=0.1, logger=mock_logger
        )

        # Open the circuit
        with pytest.raises(Exception):
            cb.call(Mock(side_effect=Exception("error")))
        assert cb._state == "OPEN"

        # Wait for recovery timeout
        time.sleep(0.2)

        # Next call should attempt recovery (half-open)
        success_func = Mock(return_value="success")
        result = cb.call(success_func)

        assert result == "success"
        assert cb._state == "CLOSED"
        assert cb._failure_count == 0


class TestConfigValidation:
    """Test configuration validation"""

    def test_validate_config_success(self):
        """Test configuration validation with valid config"""
        mock_config = Mock()
        mock_config.reddit_client_id = "valid_id"
        mock_config.reddit_client_secret = "valid_secret"
        mock_config.queue_url = "valid_url"

        # Should not raise exception
        validate_config(
            mock_config, ["reddit_client_id", "reddit_client_secret", "queue_url"]
        )

    def test_validate_config_missing_fields(self):
        """Test configuration validation with missing fields"""

        # Use a real object instead of Mock to test hasattr properly
        class TestConfig:
            reddit_client_id = "valid_id"
            # Missing reddit_client_secret

        mock_config = TestConfig()

        with pytest.raises(ConfigurationError) as exc_info:
            validate_config(mock_config, ["reddit_client_id", "reddit_client_secret"])

        assert "reddit_client_secret" in str(exc_info.value)

    def test_validate_config_invalid_values(self):
        """Test configuration validation with invalid values"""
        mock_config = Mock()
        mock_config.reddit_client_id = "MISSING_ID"  # Invalid default
        mock_config.reddit_client_secret = ""  # Empty string
        mock_config.queue_url = None  # None value

        with pytest.raises(ConfigurationError) as exc_info:
            validate_config(
                mock_config, ["reddit_client_id", "reddit_client_secret", "queue_url"]
            )

        error_msg = str(exc_info.value)
        assert "reddit_client_id" in error_msg
        assert "reddit_client_secret" in error_msg
        assert "queue_url" in error_msg


class TestCustomExceptions:
    """Test custom exception hierarchy"""

    def test_retryable_error_with_custom_delay(self):
        """Test RetryableError with custom retry delay"""
        error = RetryableError("test error", retry_after=30)

        assert str(error) == "test error"
        assert error.retry_after == 30

    def test_rate_limit_error_defaults(self):
        """Test RateLimitError with default values"""
        error = RateLimitError()

        assert "Rate limit exceeded" in str(error)
        assert error.retry_after == 300  # Default 5 minutes

    def test_rate_limit_error_custom_values(self):
        """Test RateLimitError with custom values"""
        error = RateLimitError("Custom rate limit message", retry_after=600)

        assert str(error) == "Custom rate limit message"
        assert error.retry_after == 600

    def test_configuration_error(self):
        """Test ConfigurationError"""
        error = ConfigurationError("Invalid configuration")

        assert str(error) == "Invalid configuration"
        assert isinstance(error, Exception)

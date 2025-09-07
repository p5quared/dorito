"""Custom exceptions for the application"""


class AppException(Exception):
    """Base exception for application errors"""

    pass


class DataSourceError(AppException):
    """Raised when there's an error with data sources (Reddit API, etc.)"""

    pass


class ProcessingError(AppException):
    """Raised when there's an error processing data"""

    pass


class MessageError(AppException):
    """Raised when there's an error with message handling (SQS, etc.)"""

    pass


class ConfigurationError(AppException):
    """Raised when there's a configuration error"""

    pass


class WriterError(AppException):
    """Raised when there's an error writing data"""

    pass


class RetryableError(AppException):
    """Base class for errors that can be retried"""

    def __init__(self, message: str, retry_after: int = 60):
        super().__init__(message)
        self.retry_after = retry_after


class RateLimitError(RetryableError):
    """Raised when rate limiting is encountered"""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = 300):
        super().__init__(message, retry_after)

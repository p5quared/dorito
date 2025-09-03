from abc import ABC, abstractmethod
from typing import Iterator, Any, Protocol
from .types import CommentData, PostData


class DataSource(Protocol):
    """Protocol for data sources that provide content"""

    def get_content(self, limit: int) -> Iterator[Any]:
        """Get content from the source"""
        ...


class MessageSink(ABC):
    """Abstract base class for message sinks"""

    @abstractmethod
    def send_message(self, data: str) -> None:
        """Send a message to the sink"""
        pass


class MessageSource(ABC):
    """Abstract base class for message sources"""

    @property
    @abstractmethod
    def messages(self) -> Iterator[Any]:
        """Get messages from the source"""
        pass

    @abstractmethod
    def delete_message(self, message: Any) -> None:
        """Delete a message from the source"""
        pass


class DataProcessor(ABC):
    """Abstract base class for data processors"""

    @abstractmethod
    def process(self, data: CommentData | PostData) -> dict[str, Any]:
        """Process data and return result"""
        pass


class DataWriter(ABC):
    """Abstract base class for data writers"""

    @abstractmethod
    def write(self, data: dict[str, Any]) -> None:
        """Write data to storage"""
        pass


class Logger(Protocol):
    """Protocol for logging"""

    def info(self, message: str, *args, **kwargs) -> None: ...

    def error(self, message: str, *args, **kwargs) -> None: ...

    def debug(self, message: str, *args, **kwargs) -> None: ...

    def warning(self, message: str, *args, **kwargs) -> None: ...


class ConfigProvider(Protocol):
    """Protocol for configuration"""

    @property
    def is_prod(self) -> bool: ...

    @property
    def reddit_client_id(self) -> str: ...

    @property
    def reddit_client_secret(self) -> str: ...

    @property
    def reddit_redirect_uri(self) -> str: ...

    @property
    def reddit_user_agent(self) -> str: ...

    @property
    def queue_url(self) -> str: ...

    @property
    def aws_region(self) -> str: ...

    @property
    def log_level(self) -> str: ...

import os
import logging
from typing import Optional
from .interfaces import ConfigProvider, Logger


class Config:
    """Configuration provider that reads from environment variables"""

    def __init__(self, env_override: Optional[dict] = None):
        self._env = env_override or os.environ

    @property
    def is_prod(self) -> bool:
        return self._env.get("ENVIRONMENT", "dev") == "prod"

    @property
    def reddit_client_id(self) -> str:
        return self._env.get("REDDIT_CLIENT_ID", "MISSING_ID")

    @property
    def reddit_client_secret(self) -> str:
        return self._env.get("REDDIT_SECRET", "MISSING_SECRET")

    @property
    def reddit_redirect_uri(self) -> str:
        return self._env.get("REDDIT_REDIRECT_URI", "MISSING_REDIRECT")

    @property
    def reddit_user_agent(self) -> str:
        return self._env.get("REDDIT_USER_AGENT", "MISSING_AGENT")

    @property
    def queue_url(self) -> str:
        return self._env.get("SQS_QUEUE_URL", "MISSING_QUEUE_URL")

    @property
    def aws_region(self) -> str:
        return self._env.get("AWS_REGION", "us-east-2")

    @property
    def log_level(self) -> str:
        return self._env.get("LOG_LEVEL", "INFO")

    @property
    def sns_topic_arn(self) -> str:
        return self._env.get("SNS_TOPIC_ARN", "MISSING_SNS_TOPIC_ARN")

    # Legacy properties for backward compatibility
    @property
    def client_id(self) -> str:
        return self.reddit_client_id

    @property
    def client_secret(self) -> str:
        return self.reddit_client_secret

    @property
    def redirect_uri(self) -> str:
        return self.reddit_redirect_uri

    @property
    def user_agent(self) -> str:
        return self.reddit_user_agent


class LoggingMixin:
    """Mixin for classes that need logging with proper context"""

    def __init__(self, *args, config: Optional[ConfigProvider] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._config = config or Config()
        self._setup_logging()

    def _setup_logging(self):
        """Setup logging with class-specific context"""
        logging.basicConfig(level=getattr(logging, self._config.log_level.upper()))
        self._logger = logging.getLogger(self.__class__.__name__)

    @property
    def logger(self):
        """Get logger instance with class-specific context"""
        return self._logger

    def log_info(self, message: str, *args, **kwargs):
        self._logger.info(message, *args, **kwargs)

    def log_error(self, message: str, *args, **kwargs):
        self._logger.error(message, *args, **kwargs)

    def log_debug(self, message: str, *args, **kwargs):
        self._logger.debug(message, *args, **kwargs)

    def log_warning(self, message: str, *args, **kwargs):
        self._logger.warning(message, *args, **kwargs)

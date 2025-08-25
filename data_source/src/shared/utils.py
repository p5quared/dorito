import os
import logging

class Config:
    is_prod: bool = os.getenv("ENVIRONMENT", "MISSING_ENVIRONMENt") == "prod"
    client_id: str = os.getenv("REDDIT_CLIENT_ID", "MISSING ID")
    client_secret: str = os.getenv("REDDIT_SECRET", "MISSING SECRET")
    redirect_uri: str = os.getenv("REDDIT_REDIRECT_URI", "MISSING REDIRECT")
    user_agent: str = os.getenv("REDDIT_USER_AGENT", "MISSING AGENT")
    queue_url: str = os.getenv("SQS_QUEUE_URL", "MISSING QUEUE URL")
    aws_region: str = os.getenv("AWS_REGION", "us-east-2")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


class LoggingMixin(Config):
    def __init__(self):
        super().__init__()

    @property
    def logger(self):
        if not hasattr(self, "_logger"):
            logging.basicConfig(level=super().log_level)
            self._logger = logging.getLogger(self.__class__.__name__)
        return self._logger

    def log_info(self, message: str, *args, **kwargs):
        self.logger.info(message, *args, **kwargs)

    def log_error(self, message: str, *args, **kwargs):
        self.logger.error(message, *args, **kwargs)

    def log_debug(self, message: str, *args, **kwargs):
        self.logger.debug(message, *args, **kwargs)

    def log_warning(self, message: str, *args, **kwargs):
        self.logger.warning(message, *args, **kwargs)


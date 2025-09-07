from datetime import datetime
from enum import Enum
import uuid
import json
from typing import Optional
import boto3
from botocore.exceptions import ClientError
import logging
from dataclasses import dataclass, asdict

from .utils import Config, LoggingMixin
from .interfaces import ConfigProvider, RedditDataSink
from .types import RedditData

logger = logging.getLogger(__name__)


class SourceType(Enum):
    REDDIT=1


@dataclass
class DataProducedEvent:
    correlation_id: str
    source_type: SourceType
    source_date: str
    body: RedditData
    subject: str = "Data Produced Event"
    event_type: str = "event.data.produced"

    def to_dict(self) -> dict:
        return asdict(self)

class SNSFacade(LoggingMixin, RedditDataSink):
    SOURCE: SourceType
    def __init__(self, source_type: SourceType, config: Optional[ConfigProvider] = None):
        config = config or Config()
        super().__init__(config=config)
        self.log_info(f"Initializing SNS Facade for source: {source_type.name}")
        self.SOURCE = source_type
        self._config = config
        self.sns_client = boto3.client("sns", region_name=self._config.aws_region)
        self.topic_arn = self._config.sns_topic_arn
        self.log_info(f"Initialized SNS Facade for source: {source_type.name}")
    
    def send_message(
        self,
        data: RedditData
    ):
        self.log_debug(f"Publishing event to SNS topic {self.topic_arn}")
        data_event = self.make_event(data)

        event_json = json.dumps(data_event.to_dict())

        response = self.sns_client.publish(Message=event_json)

        message_id = response.get("MessageId")
        self.log_debug(f"Successfully published event to {self.topic_arn}, MessageId: {message_id}")

        return message_id
    
    def make_event(self, body: RedditData) -> DataProducedEvent:
        return DataProducedEvent(
            correlation_id=get_correlation_id(),
            source_type=self.SOURCE,
            source_date=str(datetime.now()),
            body=body
        )

def get_correlation_id() -> str:
    return str(uuid.uuid4())

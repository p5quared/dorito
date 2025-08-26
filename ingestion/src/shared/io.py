from datetime import datetime
import boto3
from typing import Iterator, Any
from .interfaces import MessageSink, MessageSource, Logger, ConfigProvider


# MessageSource and MessageSink are now defined in interfaces.py


class PrintStrategy(MessageSink):
    def __init__(self, logger: Logger):
        self._logger = logger
        self.count = 0
        self.start_time = datetime.now()

    def send_message(self, data: str) -> None:
        self.count += 1
        run_duration = (datetime.now() - self.start_time).seconds
        rate = self.count / run_duration if run_duration > 0 else self.count
        self._logger.info(f"Process Rate: {rate} msg/sec")


class SQSStrategy(MessageSource, MessageSink):
    def __init__(self, config: ConfigProvider, logger: Logger):
        self._config = config
        self._logger = logger
        self.sqs = boto3.client("sqs", region_name=config.aws_region)
        self.queue_url = config.queue_url

    @property
    def messages(self) -> Iterator[Any]:
        try:
            while True:
                self._logger.debug("Polling SQS for messages...")
                response = self.sqs.receive_message(
                    QueueUrl=self.queue_url, MaxNumberOfMessages=5, WaitTimeSeconds=20
                )
                yield from response.get("Messages", [])
        except Exception as e:
            self._logger.error(f"Something went wrong while reading queue... {e}")
            raise

    def delete_message(self, message: Any) -> None:
        self.sqs.delete_message(
            QueueUrl=self.queue_url, ReceiptHandle=message["ReceiptHandle"]
        )

    def send_message(self, data: str) -> None:
        try:
            self.sqs.send_message(
                QueueUrl=self.queue_url,
                MessageBody=data,
            )
        except Exception as e:
            self._logger.error(f"Failed to send message to SQS: {e}")
            raise

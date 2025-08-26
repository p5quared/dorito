from datetime import datetime
import boto3
from typing import Iterator
from shared.types import CommentData, PostData
from shared.utils import LoggingMixin


class MessageSource:
    @property
    def messages(self) -> Iterator:
        raise NotImplementedError

    def delete_message(self, message):
        raise NotImplementedError


class MessageSink:
    def send_message(self, data):
        raise NotImplementedError


class PrintStrategy(MessageSink, LoggingMixin):
    def __init__(self):
        super().__init__()
        self.count = 0
        self.start_time = datetime.now()

    def send_message(self, data: CommentData | PostData):
        self.count += 1
        run_duration = (datetime.now() - self.start_time).seconds
        super().log_info(
            f"Process Rate: {self.count / run_duration if run_duration > 0 else self.count} msg/sec"
        )


class SQSStrategy(MessageSource, MessageSink, LoggingMixin):
    def __init__(self):
        self.sqs = boto3.client("sqs", region_name=super().aws_region)
        self.queue_url = super().queue_url

    @property
    def messages(self) -> Iterator[CommentData | PostData]:
        try:
            while True:
                super().log_debug("Polling SQS for messages...")
                response = self.sqs.receive_message(
                    QueueUrl=self.queue_url, MaxNumberOfMessages=5, WaitTimeSeconds=20
                )
                yield from response.get("Messages", [])
        except Exception as e:
            super().log_error(f"Something went wrong while reading queue... {e}")

    def delete_message(self, message):
        self.sqs.delete_message(
            QueueUrl=self.queue_url, ReceiptHandle=message["ReceiptHandle"]
        )

    def send_message(self, data: str):
        try:
            self.sqs.send_message(
                QueueUrl=self.queue_url,
                MessageBody=data,
            )
        except Exception as e:
            super().log_error(f"Failed to send message to SQS: {e}")
            raise e

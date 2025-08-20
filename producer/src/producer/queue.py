import boto3
from datetime import datetime

from botocore.utils import ClientError

from producer.utils import Config, LoggingMixin


class OutputAdapter(LoggingMixin, Config):
    def __init__(self) -> None:
        super().__init__()

    def send(self, data: dict):
        pass


class ProcessingQueue(OutputAdapter):
    def connect_queue(self):
        super().__init__()
        self.sqs = boto3.client("sqs")

    def send(self, data: dict):
        try:
            self.sqs.send_message(
                QueueUrl=self.queue_url,
                MessageBody=str(data),
            )
        except ClientError as e:
            super().log_error(f"Failed to send message to SQS: {e}")
            raise e


class CountQueueFacade(OutputAdapter, LoggingMixin):
    "A test class that counts messages processed and prints statistics. For local use only."

    def __init__(self):
        super().__init__()
        self.count = 0
        self.start_time = datetime.now()

    def send(self, data: dict):
        self.count += 1
        elapsed_time = (datetime.now() - self.start_time).total_seconds()
        print(
            f"\
        Total messages processed: {self.count}\n\
        Time Elapsed: {elapsed_time:.2f}s\
        Average Rate: {self.count / elapsed_time:.2f} messages/s \
        "
        )

    def connect_queue(self):
        return None

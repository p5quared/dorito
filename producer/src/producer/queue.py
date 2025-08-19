import json
import uuid
import boto3
from datetime import datetime
from botocore.exceptions import ClientError

from producer.utils import Config, LoggingMixin
from producer.reddit import CommentData, PostData

class SQSProcessingQueue(Config):
    def connect_queue(self):
        super().__init__()
        self.sqs_client = boto3.client("sqs")

    def put_messages(self, to_process: list[CommentData | PostData]):
        if not to_process:
            return

        messages = []
        for item in to_process:
            payload = {"type": type(item).__name__, "data": item.to_dict()}

            message = {"Id": str(uuid.uuid4()), "MessageBody": json.dumps(payload)}
            messages.append(message)

        batch_size = 10
        for i in range(0, len(messages), batch_size):
            batch = messages[i : i + batch_size]
            self._send_batch(batch)

    def _send_batch(self, batch: list[dict]):
        try:
            response = self.sqs_client.send_message_batch(
                QueueUrl=self.queue_url, Entries=batch
            )

            if "Failed" in response and response["Failed"]:
                for failed_msg in response["Failed"]:
                    print(
                        f"Failed to send message {failed_msg['Id']}: {failed_msg['Message']}"
                    )

            if "Successful" in response:
                print(f"Successfully sent {len(response['Successful'])} messages")

        except ClientError as e:
            print(f"Error sending batch to SQS: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise


class PrintQueueFacade(SQSProcessingQueue, LoggingMixin):
    def put_messages(self, to_process: list[CommentData | PostData]):
        for item in to_process:
            print("Putting message")
            print(f"Type: {type(item).__name__}\nData: {item.to_dict()}\n")

    def connect_queue(self):
        return None


class CountQueueFacade(SQSProcessingQueue, LoggingMixin):
    def __init__(self):
        super().__init__()
        self.count = 0
        self.start_time = datetime.now()

    def put_messages(self, to_process: list[CommentData | PostData]):
        self.count += len(to_process)
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

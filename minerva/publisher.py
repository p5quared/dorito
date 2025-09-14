import boto3
import json
from typing import Any, List, Dict, Optional


class MessagingInterface:
    def __init__(self, queue_url: str, region_name: str = "us-east-1"):
        """
        Initialize the MessagingInterface with SQS queue URL.

        Args:
            queue_url: The SQS queue URL to interact with
            region_name: AWS region name (defaults to us-east-1)
        """
        self.queue_url = queue_url
        self.sqs_client = boto3.client('sqs', region_name=region_name)

    def get_messages(self, max_messages: int = 1, wait_time_seconds: int = 20) -> List[Dict[str, Any]]:
        """
        Get messages from the SQS queue using long polling.

        Args:
            max_messages: Maximum number of messages to retrieve (1-10)
            wait_time_seconds: Long polling wait time (0-20 seconds, defaults to 20 for optimal long polling)

        Returns:
            List[Dict]: List of messages from SQS

        Raises:
            ClientError: If SQS operation fails
        """
        response = self.sqs_client.receive_message(
            QueueUrl=self.queue_url,
            MaxNumberOfMessages=min(max_messages, 10),
            WaitTimeSeconds=min(wait_time_seconds, 20),
            AttributeNames=['All'],
            MessageAttributeNames=['All']
        )

        return response.get('Messages', [])

    def delete_message(self, receipt_handle: str) -> dict:
        """
        Delete a message from the SQS queue using its receipt handle.

        Args:
            receipt_handle: The receipt handle of the message to delete

        Returns:
            dict: SQS delete_message response

        Raises:
            ClientError: If SQS operation fails
        """
        response = self.sqs_client.delete_message(
            QueueUrl=self.queue_url,
            ReceiptHandle=receipt_handle
        )

        return response

    def publish(self, message_body: str) -> dict:
        """
        Publish a message to the SQS queue.

        Args:
            message_body: The message body as a JSON string

        Returns:
            dict: SQS send_message response

        Raises:
            ClientError: If SQS operation fails
        """
        response = self.sqs_client.send_message(
            QueueUrl=self.queue_url,
            MessageBody=message_body
        )

        return response


class PrintMessagingInterface:
    def __init__(self):
        """
        Initialize the PrintMessagingInterface for testing/debugging.
        """
        self._mock_messages: List[Dict[str, Any]] = []

    def get_messages(self, max_messages: int = 1, wait_time_seconds: int = 0) -> List[Dict[str, Any]]:
        """
        Get mock messages from the print interface.

        Args:
            max_messages: Maximum number of messages to retrieve (1-10)
            wait_time_seconds: Wait time (ignored in print mode)

        Returns:
            List[Dict]: List of mock messages
        """
        messages = self._mock_messages[:min(max_messages, 10)]
        print(f"📥 Getting {len(messages)} message(s) from queue")
        for msg in messages:
            print(json.dumps(msg, indent=2))
        return messages

    def delete_message(self, receipt_handle: str) -> dict:
        """
        Delete a mock message using its receipt handle.

        Args:
            receipt_handle: The receipt handle of the message to delete

        Returns:
            dict: Mock delete response
        """
        print(f"🗑️ Deleting message with receipt handle: {receipt_handle}")
        self._mock_messages = [msg for msg in self._mock_messages if msg.get('ReceiptHandle') != receipt_handle]

        return {
            'ResponseMetadata': {
                'HTTPStatusCode': 200
            }
        }

    def publish(self, message_body: str) -> dict:
        """
        Print the message instead of publishing to SQS.

        Args:
            message_body: The message body as a JSON string

        Returns:
            dict: Mock response similar to SQS send_message response
        """
        receipt_handle = f"print-receipt-{len(self._mock_messages)}"

        mock_message = {
            'MessageId': f'print-message-{len(self._mock_messages)}',
            'ReceiptHandle': receipt_handle,
            'Body': message_body,
            'Attributes': {},
            'MessageAttributes': {}
        }
        self._mock_messages.append(mock_message)

        print("📤 Publishing message:")
        print(json.dumps(json.loads(message_body), indent=2))

        return {
            'MessageId': mock_message['MessageId'],
            'MD5OfBody': 'mock-md5-hash',
            'ResponseMetadata': {
                'HTTPStatusCode': 200
            }
        }


class MessagingInterfaceBuilder:
    def __init__(self):
        self._queue_url: Optional[str] = None
        self._region_name: Optional[str] = None

    def with_queue_url(self, url: str) -> 'MessagingInterfaceBuilder':
        """Set the SQS queue URL."""
        self._queue_url = url
        return self

    def with_region(self, region_name: str) -> 'MessagingInterfaceBuilder':
        """Set the AWS region name."""
        self._region_name = region_name
        return self

    def build(self) -> MessagingInterface:
        """Build and return a MessagingInterface instance."""
        if self._queue_url is None:
            raise ValueError("Queue URL is required")
        if self._region_name is None:
            raise ValueError("Region name is required")

        return MessagingInterface(
            queue_url=self._queue_url,
            region_name=self._region_name
        )

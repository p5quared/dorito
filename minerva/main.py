import json
import os

from message_types import KeyWordResult, RawDataProducedEvent
from kw import KeywordWorker
from publisher import MessagingInterfaceBuilder, PrintMessagingInterface

HANDLERS = {}

def register_handler(name: str):
    """Decorator to register handlers"""
    def decorator(func):
        HANDLERS[name] = func
        return func
    return decorator

AWS_REGION = os.getenv('AWS_REGION', 'us-east-2')
OUTPUT_QEUE_URL = os.getenv('OUTPUT_QUEUE_URL', 'MISSING')
INPUT_QUEUE_URL = os.getenv('INPUT_QUEUE_URL', 'MISSING')


@register_handler('KEYWORD')
def keyword_handler(body):
    # print(body)
    raw_data = RawDataProducedEvent(**body)
    kws = KeywordWorker().process(raw_data.data.body)
    kws = [{'keyword': kw, 'confidence': float(conf)} for kw, conf in kws]
    kws_publishable = [KeyWordResult(**kw) for kw in kws]
    kw_publisher = MessagingInterfaceBuilder().with_region(AWS_REGION).with_queue_url(OUTPUT_QEUE_URL).build()
    print(raw_data.data.body)
    kw_publisher = PrintMessagingInterface()
    for kw in kws_publishable:
        kw_publisher.publish(kw.model_dump_json())
    print("=" * 40)

def ecs_handler(batch_size: int = 10, wait_time_seconds: int = 20):
    """
    ECS handler that polls SQS for messages and processes them using registered handlers.

    Args:
        batch_size: Maximum number of messages to retrieve in each poll (1-10)
        wait_time_seconds: SQS long polling wait time (0-20 seconds)
        poll_interval: Time to wait between polling cycles when no messages received (seconds)
    """
    service_type = os.getenv('SERVICE_TYPE', 'MISSING_SERVICE_TYPE')

    if service_type not in HANDLERS:
        print(f"Error: Unknown service type '{service_type}'. Available handlers: {list(HANDLERS.keys())}")
        return

    handler = HANDLERS[service_type]

    input_queue = MessagingInterfaceBuilder()\
        .with_region(AWS_REGION)\
        .with_queue_url(INPUT_QUEUE_URL)\
        .build()

    print(f"Starting ECS handler for service type: {service_type}")
    print(f"Polling configuration: batch_size={batch_size}, wait_time={wait_time_seconds}s")
    print(f"Input queue: {INPUT_QUEUE_URL}")

    for _ in range(1):
        try:
            messages = input_queue.get_messages(
                max_messages=batch_size,
                wait_time_seconds=wait_time_seconds
            )

            print(f"Received {len(messages)} message(s), processing...")

            successfully_processed = []
            for message in messages:
                try:
                    body = json.loads(message['Body'])
                    message_id = message.get('MessageId', 'unknown')
                    receipt_handle = message['ReceiptHandle']

                    print(f"Processing message {message_id}")

                    handler(body)

                    successfully_processed.append(receipt_handle)
                    print(f"Successfully processed message {message_id}")

                except json.JSONDecodeError as e:
                    print(f"Error parsing message JSON: {e}")
                    print(f"Message body: {message.get('Body', 'N/A')}")
                except Exception as e:
                    print(f"Error processing message {message.get('MessageId', 'unknown')}: {e}")
                    print(f"Message body: {message.get('Body', 'N/A')}")
            for receipt_handle in successfully_processed:
                try:
                    input_queue.delete_message(receipt_handle)
                except Exception as e:
                    print(f"Error deleting message with receipt handle {receipt_handle}: {e}")
            print(f"Processed batch: {len(successfully_processed)}/{len(messages)} successful")
        except KeyboardInterrupt:
            print("\nReceived interrupt signal, shutting down gracefully...")

def main():
    ecs_handler()

if __name__ == "__main__":
    main()

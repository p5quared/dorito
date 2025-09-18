import time
import json
import os

from embedding import EmbeddingWorker
from message_types import EmbeddingResult, KeyWordProducedEvent, KeyWordResult, PyABSAResult, RawDataProducedEvent, PyABSAProducedEvent
from kw import KeywordWorker
from pyabsa_handler import PyABSAWorker
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
    raw_data = RawDataProducedEvent(**body)
    kws = KeywordWorker().process(raw_data.data.body)
    kws = [{'keyword': kw, 'confidence': float(conf)} for kw, conf in kws]
    kws_publishable = [KeyWordResult(**kw) for kw in kws]
    kw_publisher = MessagingInterfaceBuilder().with_region(AWS_REGION).with_queue_url(OUTPUT_QEUE_URL).build()
    kw_publisher = PrintMessagingInterface()
    for kw in kws_publishable:
        kw_publisher.publish(kw.model_dump_json())

@register_handler('EMBED')
def embed_handler(body):
    kw_data = KeyWordProducedEvent(**body)
    embedding = EmbeddingWorker().embed(kw_data.data.keyword)
    embeddings_publishable = EmbeddingResult(keyword=kw_data.data.keyword, embedding=embedding)
    embed_publisher = MessagingInterfaceBuilder().with_region(AWS_REGION).with_queue_url(OUTPUT_QEUE_URL).build()
    embed_publisher.publish(embeddings_publishable.model_dump_json())

@register_handler('PYABSA')
def pyabsa_handler(body):
    raw_data = RawDataProducedEvent(**body)
    result = PyABSAWorker().process(raw_data.data.body)
    if not result:
        return
    for asp, sent, conf in zip(result['aspect'], result['sentiment'], result['confidence']):
        sent_int = 0
        if sent == 'Postiive':
            sent_int = 1
        elif sent == 'Negative':
            sent_int = -1
        pyabsa_result = PyABSAResult(keyword=asp, sentiment=sent_int, confidence=conf)
        pyabsa_publishable = PyABSAProducedEvent(meta=raw_data.meta, data=pyabsa_result)
        pyabsa_publisher = MessagingInterfaceBuilder().with_region(AWS_REGION).with_queue_url(OUTPUT_QEUE_URL).build()
        pyabsa_publisher.publish(pyabsa_publishable.model_dump_json())

def ecs_handler(batch_size: int = 10, wait_time_seconds: int = 5):
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

    while True:
        try:
            messages = input_queue.get_messages(
                max_messages=batch_size,
                wait_time_seconds=wait_time_seconds
            )

            print(f"Received {len(messages)} message(s), processing...")

            batch_start = time.time()
            successfully_processed = []
            for message in messages:
                try:
                    body = json.loads(message['Body'])
                    message_id = message.get('MessageId', 'unknown')
                    receipt_handle = message['ReceiptHandle']

                    print(f"Processing message {message_id}")

                    msg_start = time.time()
                    handler(body)
                    print(f"Processing time for message {message_id}: {time.time() - msg_start:.2f} seconds")

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
            print(f"Batch processing time: {time.time() - batch_start:.2f} seconds for {len(messages)} message(s)")
        except KeyboardInterrupt:
            print("\nReceived interrupt signal, shutting down gracefully...")
            break

def main():
    ecs_handler()

if __name__ == "__main__":
    main()

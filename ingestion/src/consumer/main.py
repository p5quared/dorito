from .processor import FinancialRelevanceProcessor
from .utils import CSVDataWriter
from shared.io import SQSStrategy
from shared.types import deserialize_reddit_data, get_post_comment_csv_columns
from shared.interfaces import (
    MessageSource,
    DataProcessor,
    DataWriter,
    Logger,
    ConfigProvider,
)
from shared.container import DIContainer, create_container


class ConsumerApplication:
    """Main application for consuming and processing Reddit data"""

    def __init__(
        self,
        message_source: MessageSource,
        processor: DataProcessor,
        writer: DataWriter,
        logger: Logger,
    ):
        self._message_source = message_source
        self._processor = processor
        self._writer = writer
        self._logger = logger

    def run(self) -> None:
        """Run the consumer application"""
        self._logger.info("Starting Consumer Application")
        try:
            self._loop()
        except Exception as e:
            self._logger.error(f"An error occurred: {e}")
            raise
        finally:
            self._logger.info("Shutting down Consumer Application")
            self._writer.flush()

    def _loop(self) -> None:
        """Main processing loop"""
        processed_count = 0

        try:
            for message in self._message_source.messages:
                try:
                    data = deserialize_reddit_data(message["Body"])
                    result = self._processor.process(data)

                    if result:  # Only write non-empty results
                        self._writer.write(result)

                    self._message_source.delete_message(message)
                    processed_count += 1

                    if processed_count % 100 == 0:
                        self._logger.info(f"Processed {processed_count} messages...")

                except Exception as e:
                    self._logger.error(f"Error processing message: {e}")
                    # Still delete the message to avoid reprocessing bad data
                    self._message_source.delete_message(message)

        except KeyboardInterrupt:
            self._logger.info("Received interrupt signal, shutting down gracefully...")
        except Exception as e:
            self._logger.error(f"Fatal error in processing loop: {e}")
            raise
        finally:
            self._writer.flush()

def create_local_consumer(container: DIContainer) -> ConsumerApplication:
    """Create local consumer application"""
    logger = container.get(Logger)
    config = container.get(ConfigProvider)

    message_source = SQSStrategy(config, logger)
    processor = FinancialRelevanceProcessor(logger)
    writer = CSVDataWriter(
        "data.csv", buffer_size=5, fieldnames=get_post_comment_csv_columns()
    )

    logger.info("Running in Local Mode")
    return ConsumerApplication(message_source, processor, writer, logger)


def create_prod_consumer(container: DIContainer) -> ConsumerApplication:
    """Create production consumer application"""
    logger = container.get(Logger)
    config = container.get(ConfigProvider)

    message_source = SQSStrategy(config, logger)
    processor = FinancialRelevanceProcessor(logger)
    writer = CSVDataWriter(
        "data.csv", buffer_size=5, fieldnames=get_post_comment_csv_columns()
    )

    logger.info("Running in Production Mode")
    return ConsumerApplication(message_source, processor, writer, logger)

def main():

    container = create_container()
    config = container.get(ConfigProvider)

    if config.is_prod:
        app = create_prod_consumer(container)
    else:
        app = create_local_consumer(container)

    app.run()

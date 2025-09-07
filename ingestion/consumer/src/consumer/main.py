from .processor import FinancialRelevanceProcessor
from .utils import CSVDataWriter
from shared.io import SQSStrategy
from shared.types import deserialize_reddit_data, get_post_comment_csv_columns
from shared.interfaces import (
    MessageSource,
    DataProcessor,
    DataWriter,
    ConfigProvider,
)
from shared.container import DIContainer, create_container
from shared.utils import LoggingMixin


class ConsumerApplication(LoggingMixin):
    """Main application for consuming and processing Reddit data"""

    def __init__(
        self,
        message_source: MessageSource,
        processor: DataProcessor,
        writer: DataWriter,
        config: ConfigProvider,
    ):
        super().__init__(config=config)
        self._message_source = message_source
        self._processor = processor
        self._writer = writer

    def run(self) -> None:
        """Run the consumer application"""
        self.log_info("Starting Consumer Application")
        try:
            self._loop()
        except Exception as e:
            self.log_error(f"An error occurred: {e}")
            raise
        finally:
            self.log_info("Shutting down Consumer Application")

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
                        self.log_info(f"Processed {processed_count} messages...")

                except Exception as e:
                    self.log_error(f"Error processing message: {e}")
                    # Still delete the message to avoid reprocessing bad data
                    self._message_source.delete_message(message)

        except KeyboardInterrupt:
            self.log_info("Received interrupt signal, shutting down gracefully...")
        except Exception as e:
            self.log_error(f"Fatal error in processing loop: {e}")
            raise

def create_local_consumer(container: DIContainer) -> ConsumerApplication:
    """Create local consumer application"""
    config = container.get(ConfigProvider)

    message_source = SQSStrategy(config)
    processor = FinancialRelevanceProcessor(config)
    writer = CSVDataWriter(
        "data.csv", fieldnames=get_post_comment_csv_columns()
    )

    app = ConsumerApplication(message_source, processor, writer, config)
    app.log_info("Running in Local Mode")
    return app


def create_prod_consumer(container: DIContainer) -> ConsumerApplication:
    """Create production consumer application"""
    config = container.get(ConfigProvider)

    message_source = SQSStrategy(config)
    processor = FinancialRelevanceProcessor(config)
    writer = CSVDataWriter(
        "dataV2.csv", fieldnames=get_post_comment_csv_columns()
    )

    app = ConsumerApplication(message_source, processor, writer, config)
    app.log_info("Running in Production Mode")
    return app

def main():

    container = create_container()
    config = container.get(ConfigProvider)

    if config.is_prod:
        app = create_prod_consumer(container)
    else:
        app = create_local_consumer(container)

    app.run()

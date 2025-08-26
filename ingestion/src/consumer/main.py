from consumer.processor import Processor, RedditDataProcessor
from consumer.utils import LocalCSVWriter, Writer
from shared.io import MessageSource, SQSStrategy
from shared.types import deserialize_reddit_data, get_post_comment_csv_columns
from shared.utils import Config, LoggingMixin


class ConsumerApplication(MessageSource, Processor, LoggingMixin):
    def __init__(self, w: Writer):
        self.writer = w
        super().__init__()

    def run(self):
        super().log_info("Starting Consumer Application")
        try:
            self._loop()
        except Exception as e:
            super().log_error(f"An error occurred: {e}")
        finally:
            super().log_info("Shutting down Consumer Application")
            self.writer.flush()

    def _loop(self):
        processed_count = 0
        for message in super().messages:
            data = deserialize_reddit_data(message["Body"])
            if result := super().process(data):
                self.writer.write(result)
            super().delete_message(message)
            processed_count += 1
            if processed_count % 100 == 0:
                super().log_info(f"Processed {processed_count} messages...")


class LocalConsumerApplication(ConsumerApplication, SQSStrategy, RedditDataProcessor):
    def __init__(self, w: Writer):
        super().__init__(w=w)
        super().log_info("Initialized LocalConsumerApplication")

    def run(self):
        super().log_info("Running in Local Mode")
        super().run()


class ContainerConsumerApplication(
    ConsumerApplication, RedditDataProcessor, SQSStrategy
):
    def __init__(self, w: Writer):
        super().__init__(w=w)
        super().log_info("Initialized ProdConsumerApplication")

    def run(self):
        super().log_info("Running in Production Mode")
        super().run()


def app_factory(cfg):
    w = LocalCSVWriter(
        "data.csv", buffer_size=5, fieldnames=get_post_comment_csv_columns()
    )
    if cfg.is_prod:
        return ContainerConsumerApplication(w)
    return LocalConsumerApplication(w)


def main():
    app = app_factory(Config())
    app.run()

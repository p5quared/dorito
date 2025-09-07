import itertools
import random
from typing import List

from shared.sns import SNSFacade, SourceType
from shared.types import RedditData

from .reddit import FINANCE_SUBREDDITS, PrawClient, SubredditDataSource
from shared.io import PrintStrategy
from shared.interfaces import RedditDataSink, ConfigProvider
from shared.container import DIContainer, create_container
from shared.utils import LoggingMixin


class RedditScraperApplication(LoggingMixin):
    """Main application for scraping Reddit data"""

    def __init__(
        self,
        message_sink: RedditDataSink,
        config: ConfigProvider,
    ):
        super().__init__(config=config)
        self._message_sink = message_sink
        self._config = config

    def run(self) -> None:
        """Run the scraper application"""
        self.log_info("Starting Producer Application")
        subreddits = FINANCE_SUBREDDITS.copy()
        random.shuffle(subreddits)

        source_classes = map(self.create_subreddit_data_source, subreddits)
        sources = map(lambda s: s.data(), source_classes)
        praw_data = itertools.chain.from_iterable(sources)
        reddit_data = map(RedditData.from_reddit_item, praw_data)
        list(map(self._message_sink.send_message, reddit_data))

        self.log_info("Producer Application Finished")


    def create_subreddit_data_source(self, n: str) -> SubredditDataSource:
        reddit_client = PrawClient(self._config)
        scrape_limit = 25
        return SubredditDataSource(n, reddit_client, self._config, scrape_limit)

def create_prod_application(container: DIContainer) -> RedditScraperApplication:
    """Create production scraper application"""
    config = container.get(ConfigProvider)

    message_sink = SNSFacade(SourceType.REDDIT, config)

    app = RedditScraperApplication(message_sink, config)
    app.log_info("Running in Production Mode")
    return app


def create_local_application(container: DIContainer) -> RedditScraperApplication:
    """Create local scraper application"""
    config = container.get(ConfigProvider)

    message_sink = PrintStrategy(config)

    app = RedditScraperApplication(message_sink, config)
    app.log_info("Running in Local Mode")
    return app

def main():
    """Main entry point"""

    container = create_container()
    config = container.get(ConfigProvider)

    if config.is_prod:
        app = create_prod_application(container)
    else:
        app = create_local_application(container)

    app.run()

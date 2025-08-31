import random
from typing import List

from .reddit import FINANCE_SUBREDDITS, SubredditDataSource, PrawClient
from shared.io import PrintStrategy, SQSStrategy
from shared.types import CommentData, PostData
from shared.interfaces import MessageSink, Logger, ConfigProvider
from shared.container import DIContainer


class RedditScraperApplication:
    """Main application for scraping Reddit data"""

    def __init__(
        self,
        message_sink: MessageSink,
        reddit_client: PrawClient,
        logger: Logger,
        subreddits: List[str] = [],
    ):
        self._message_sink = message_sink
        self._reddit_client = reddit_client
        self._logger = logger
        self._subreddits = subreddits or FINANCE_SUBREDDITS.copy()

    def run(self) -> None:
        """Run the scraper application"""
        self._logger.info("Starting Producer Application")
        try:
            self._loop()
        except Exception as e:
            self._logger.error(f"An error occurred: {e}")
            raise

    def _loop(self) -> None:
        """Main processing loop"""
        subreddits = self._subreddits.copy()
        random.shuffle(subreddits)
        content_count = 0

        for idx, subreddit_name in enumerate(subreddits):
            self._logger.info(
                f"Processing subreddit {idx + 1}/{len(subreddits)}: {subreddit_name}..."
            )

            data_source = SubredditDataSource(
                subreddit_name, self._reddit_client, self._logger
            )
            posts = data_source.get_content(limit=25)

            for post in posts:
                content_count += 1
                post_data = PostData.from_submission(post)
                self._message_sink.send_message(post_data.to_json())

                comments = data_source.get_comments_from_submission(post)
                for comment in comments:
                    content_count += 1
                    comment_data = CommentData.from_comment(comment)
                    self._message_sink.send_message(comment_data.to_json())

                self._logger.debug(f"Finished processing post: {post.id}")
                self._logger.debug(
                    f"Total content items processed so far: {content_count}"
                )

            self._logger.info(f"Finished processing: {subreddit_name}...")
            self._logger.info(f"Total content items processed so far: {content_count}")


# Legacy classes - deprecated, use factory functions instead
class ProdScraperApplication(RedditScraperApplication):
    """Deprecated - use create_prod_application instead"""

    pass


class LocalScraperApplication(RedditScraperApplication):
    """Deprecated - use create_local_application instead"""

    pass


def create_prod_application(container: DIContainer) -> RedditScraperApplication:
    """Create production scraper application"""
    config = container.get(ConfigProvider)
    logger = container.get(Logger)

    message_sink = SQSStrategy(config, logger)
    reddit_client = PrawClient(config)

    logger.info("Running in Production Mode")
    return RedditScraperApplication(message_sink, reddit_client, logger)


def create_local_application(container: DIContainer) -> RedditScraperApplication:
    """Create local scraper application"""
    logger = container.get(Logger)

    message_sink = PrintStrategy(logger)
    reddit_client = PrawClient(container.get(ConfigProvider))

    logger.info("Running in Local Mode")
    return RedditScraperApplication(message_sink, reddit_client, logger)


def app_factory(cfg) -> RedditScraperApplication:
    """Legacy factory function - deprecated"""
    from shared.container import create_container

    container = create_container()

    if cfg.is_prod:
        return create_prod_application(container)
    return create_local_application(container)


def main():
    """Main entry point"""
    from shared.container import create_container

    container = create_container()
    config = container.get(ConfigProvider)

    if config.is_prod:
        app = create_prod_application(container)
    else:
        app = create_local_application(container)

    app.run()

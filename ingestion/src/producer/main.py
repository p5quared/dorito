import random

from producer.reddit import FINANCE_SUBREDDITS, SubredditFacade
from shared.io import MessageSink, PrintStrategy, SQSStrategy
from shared.types import CommentData, PostData
from shared.utils import Config, LoggingMixin


class RedditScraperApplication(MessageSink, LoggingMixin):
    def __init__(self):
        super().__init__()

    def run(self):
        super().log_info("Starting Producer Application")
        try:
            self._loop()
        except Exception as e:
            super().log_error(f"An error occurred: {e}")

    def _loop(self):
        random.shuffle(FINANCE_SUBREDDITS)
        content_count = 0
        for idx, next_subreddit in enumerate(FINANCE_SUBREDDITS):
            super().log_info(
                f"Processing subreddit {idx + 1}/{len(FINANCE_SUBREDDITS)}: {next_subreddit}..."
            )
            reddit = SubredditFacade(next_subreddit)
            posts = reddit.get_hot_submissions(limit=25)
            for post in posts:
                content_count += 1
                super().send_message(PostData.from_submission(post).to_json())
                comments = reddit.get_all_comments_from_submission(post)
                for comment in comments:
                    content_count += 1
                    super().send_message(CommentData.from_comment(comment).to_json())
                super().log_info(f"Finished processing post: {post.id}")
                super().log_info(
                    f"Total content items processed so far: {content_count}"
                )
            super().log_info(f"Finished processing: {next_subreddit}...")
            super().log_info(f"Total content items processed so far: {content_count}")


class ProdScraperApplication(RedditScraperApplication, SQSStrategy):
    def run(self):
        super().log_info("Running in Production Mode")
        super().run()


class LocalScraperApplication(RedditScraperApplication, PrintStrategy):
    def run(self):
        super().log_info("Running in Local Mode")
        super().run()


def app_factory(cfg):
    if cfg.is_prod:
        return ProdScraperApplication()
    return LocalScraperApplication()


def main():
    app = app_factory(Config())
    app.run()

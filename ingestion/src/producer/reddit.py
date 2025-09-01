import praw
from praw.models import Submission, Comment
import itertools
from typing import Iterator

from shared.interfaces import ConfigProvider, Logger, DataSource

FINANCE_SUBREDDITS = [
    "finance",
    "personalfinance",
    "CryptoCurrency",
    "wallstreetbets",
    "stocks",
    "Bogleheads",
    "algotrading",
    "investing",
]


class PrawClient:
    """Reddit API client wrapper"""

    def __init__(self, config: ConfigProvider):
        self._config = config
        self.reddit = praw.Reddit(
            client_id=config.reddit_client_id,
            client_secret=config.reddit_client_secret,
            redirect_uri=config.reddit_redirect_uri,
            user_agent=config.reddit_user_agent,
            ratelimit_seconds=1200,
        )


class SubredditDataSource(DataSource):
    """Data source for Reddit subreddit content"""

    def __init__(self, subreddit: str, reddit_client: PrawClient, logger: Logger):
        self._subreddit = subreddit
        self._reddit_client = reddit_client
        self._logger = logger

    def get_content(self, limit: int = 25) -> Iterator[Submission]:
        """Get hot submissions from the subreddit"""
        self._logger.info(
            f"Fetching hot submissions from subreddit: {self._subreddit} with limit: {limit}"
        )
        posts = self._reddit_client.reddit.subreddit(self._subreddit).hot(limit=limit)
        return itertools.islice(posts, limit)

    def get_comments_from_submission(self, submission: Submission) -> list[Comment]:
        """Get all comments from a submission"""
        self._logger.info(f"Fetching all comments from submission: {submission.id}")
        submission.comments.replace_more(limit=None)
        return [
            comment
            for comment in submission.comments.list()
            if isinstance(comment, Comment)
        ]

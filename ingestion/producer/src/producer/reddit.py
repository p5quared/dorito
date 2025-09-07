import praw
from praw.models import Submission, Comment
import itertools
from typing import Iterator, Union

from shared.interfaces import ConfigProvider, DataSource
from shared.utils import LoggingMixin

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


class SubredditDataSource(LoggingMixin, DataSource):
    """Data source for Reddit subreddit content"""

    def __init__(self, subreddit: str, reddit_client: PrawClient, config: ConfigProvider, post_limit: int = 25):
        super().__init__(config=config)
        self._subreddit = subreddit
        self._reddit_client = reddit_client
        self._post_limit = post_limit

    def get_content(self, limit: int = 25) -> Iterator[Submission]:
        """Get hot submissions from the subreddit"""
        self.log_info(
            f"Fetching hot submissions from subreddit: {self._subreddit} with limit: {limit}"
        )
        posts = self._reddit_client.reddit.subreddit(self._subreddit).hot(limit=limit)
        return itertools.islice(posts, limit)

    def get_comments_from_submission(self, submission: Submission) -> list[Comment]:
        """Get all comments from a submission"""
        self.log_info(f"Fetching all comments from submission: {submission.id}")
        submission.comments.replace_more(limit=None)
        return [
            comment
            for comment in submission.comments.list()
            if isinstance(comment, Comment)
        ]

    def data(self) -> Iterator[Submission | Comment]:
        """Yield all posts and comments one by one"""
        self.log_info(
            f"Fetching all content from subreddit: {self._subreddit} with post limit: {self._post_limit}"
        )
        posts = self._reddit_client.reddit.subreddit(self._subreddit).hot(limit=self._post_limit)
        
        for post in itertools.islice(posts, self._post_limit):
            yield post
            yield from self.get_comments_from_submission(post)


def create_subreddit_data_source(subreddit: str, scrape_limit: int, config: ConfigProvider) -> SubredditDataSource:
    """Factory function to create a SubredditDataSource"""
    reddit_client = PrawClient(config)
    return SubredditDataSource(subreddit, reddit_client, config, scrape_limit)

import praw
from praw.models import Submission, Comment
import itertools

from shared.utils import Config, LoggingMixin

FINANCE_SUBREDDITS = [
    "finance",
    "personalfinance",
    "CryptoCurrency",
    "wallstreetbets",
    "stocks",
    "Bogleheads",
    "stocks",
    "algotrading",
    "investing",
]


class PrawClient(Config):
    reddit: praw.Reddit

    def __init__(self):
        super().__init__()
        self.reddit = praw.Reddit(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            user_agent=self.user_agent,
            ratelimit_seconds=600,
        )


class SubredditFacade(PrawClient, LoggingMixin):
    def __init__(self, subreddit):
        super().__init__()
        self.subreddit = subreddit

    def get_hot_submissions(self, limit: int = 25):
        self.log_info(
            f"Fetching hot submissions from subreddit: {self.subreddit} with limit: {limit}"
        )
        posts = self.reddit.subreddit(self.subreddit).hot(limit=limit)
        return itertools.islice(posts, limit)

    def get_all_comments_from_submission(self, submission: Submission) -> list[Comment]:
        self.log_info(f"Fetching all comments from submission: {submission.id}")
        submission.comments.replace_more(limit=None)
        return [
            comment
            for comment in submission.comments.list()
            if isinstance(comment, Comment)
        ]

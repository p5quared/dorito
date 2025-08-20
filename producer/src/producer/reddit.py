import praw
from praw.models import Submission, Comment
import itertools

from producer.utils import Config, LoggingMixin

FINANCE_SUBREDDITS = [
    "finance",
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
            ratelimit_seconds=120,
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


class PostData:
    def __init__(self, submission: Submission):
        self.id = submission.id
        self.title = submission.title
        self.score = submission.score
        self.permalink = submission.permalink
        self.created_utc = submission.created_utc

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "score": self.score,
            "permalink": self.permalink,
            "created_utc": self.created_utc,
        }


class CommentData:
    def __init__(self, comment: Comment):
        self.id = comment.id
        self.submission_id = comment.submission.id if comment.submission else "unknown"
        self.parent_id = comment.parent_id if comment.parent_id else "unknown"
        self.body = comment.body
        self.score = comment.score
        self.permalink = comment.permalink
        self.created_utc = comment.created_utc

    def to_dict(self):
        return {
            "id": self.id,
            "submission_id": self.submission_id,
            "parent_id": self.parent_id,
            "body": self.body,
            "score": self.score,
            "permalink": self.permalink,
            "created_utc": self.created_utc,
        }

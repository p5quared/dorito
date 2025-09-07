import json
from dataclasses_json import dataclass_json
from dataclasses import dataclass, fields
from praw.models import Comment, Submission


@dataclass
class RedditData:
    submission_id: str
    subreddit: str
    body: str

    @classmethod
    def from_submission(cls, submission: Submission):
        return cls(
            submission_id=submission.id,
            subreddit=submission.subreddit.display_name,
            body=submission.selftext
        )

    @classmethod
    def from_comment(cls, comment: Comment):
        return cls(
            submission_id=comment.submission.id if comment.submission else "unknown",
            subreddit=comment.subreddit.display_name if comment.subreddit else "unknown",
            body=comment.body
        )

    @classmethod
    def from_reddit_item(cls, item: Submission | Comment):
        """Convert from either a Submission or Comment"""
        if isinstance(item, Submission):
            return cls.from_submission(item)
        elif isinstance(item, Comment):
            return cls.from_comment(item)
        else:
            raise ValueError(f"Unsupported Reddit item type: {type(item)}")


@dataclass_json
@dataclass
class PostData:
    id: str
    subreddit: str
    body: str
    score: int
    message_t: str = "post"

    @classmethod
    def from_submission(cls, submission: Submission):
        return cls(
            id=submission.id,
            subreddit=submission.subreddit.display_name,
            score=submission.score,
            body=submission.selftext,
        )


@dataclass_json
@dataclass
class CommentData:
    id: str
    subreddit: str
    body: str
    score: int
    submission_id: str = "unknown"
    parent_id: str = "unknown"
    message_t: str = "comment"

    @classmethod
    def from_comment(cls, comment: Comment):
        return cls(
            id=comment.id,
            submission_id=comment.submission.id if comment.submission else "unknown",
            parent_id=comment.parent_id if comment.parent_id else "unknown",
            score=comment.score,
            subreddit=comment.subreddit.display_name
            if comment.subreddit
            else "unknown",
            body=comment.body,
        )


def get_post_comment_csv_columns() -> list[str]:
    post_fields = {field.name for field in fields(PostData)}
    comment_fields = {field.name for field in fields(CommentData)}
    all_fields = sorted(post_fields | comment_fields)
    return list(all_fields)


def deserialize_reddit_data(json_str: str) -> PostData | CommentData:
    data = json.loads(json_str)
    message_type = data.get("message_t")

    if message_type == "post":
        return PostData.from_json(json_str)  # pyright: ignore (from @dataclass_json)
    elif message_type == "comment":
        return CommentData.from_json(json_str)  # pyright: ignore (from @dataclass_json)
    else:
        raise ValueError(f"Unknown message type: {message_type}")

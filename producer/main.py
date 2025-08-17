import praw
import praw.models
import os
import itertools
from dataclasses import dataclass
import boto3
import json
import uuid
from datetime import datetime
from botocore.exceptions import ClientError

class LoggingMixin:
    @property
    def logger(self):
        if not hasattr(self, '_logger'):
            import logging
            logging.basicConfig(level=logging.INFO)
            self._logger = logging.getLogger(self.__class__.__name__)
        return self._logger
    
    def log_info(self, message: str, *args, **kwargs):
        self.logger.info(message, *args, **kwargs)
    
    def log_error(self, message: str, *args, **kwargs):
        self.logger.error(message, *args, **kwargs)
    
    def log_debug(self, message: str, *args, **kwargs):
        self.logger.debug(message, *args, **kwargs)
    
    def log_warning(self, message: str, *args, **kwargs):
        self.logger.warning(message, *args, **kwargs)

@dataclass
class Config:
    is_prod: bool =  os.getenv("ENVIRONMENT", "MISSING_ENVIRONMENt") == "PRODUCTION"
    client_id: str =  os.getenv("REDDIT_CLIENT_ID", "MISSING ID")
    client_secret: str = os.getenv("REDDIT_SECRET", "MISSING SECRET")
    redirect_uri: str = os.getenv("REDDIT_REDIRECT_URI", "MISSING REDIRECT")
    user_agent: str = os.getenv("REDDIT_USER_AGENT", "MISSING AGENT")
    queue_url: str = os.getenv("SQS_QUEUE_URL", "MISSING QUEUE URL")

class PrawClient(Config):
    reddit: praw.Reddit
    def __init__(self):
        super().__init__()
        self.reddit = praw.Reddit(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            user_agent=self.user_agent,
            ratelimit_seconds=120
        )

class SubredditFacade(PrawClient, LoggingMixin):
    def __init__(self, subreddit):
        super().__init__()
        self.subreddit = subreddit

    def get_hot_submissions(self, limit: int = 25):
        self.log_info(f"Fetching hot submissions from subreddit: {self.subreddit} with limit: {limit}")
        posts = self.reddit.subreddit(self.subreddit).hot(limit=limit)      
        return itertools.islice(posts, limit)

    def get_all_comments_from_submission(self, submission: praw.models.Submission)-> list[praw.models.Comment]:
        self.log_info(f"Fetching all comments from submission: {submission.id}")
        submission.comments.replace_more(limit=None)
        return [comment for comment in submission.comments.list() if isinstance(comment, praw.models.Comment)]

class PostData:
    def __init__(self, submission: praw.models.Submission):
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
            "created_utc": self.created_utc
        }

class CommentData:
    def __init__(self, comment: praw.models.Comment):
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
            "created_utc": self.created_utc
        }


class SQSProcessingQueue(Config):
    def connect_queue(self):
        super().__init__()
        self.sqs_client = boto3.client('sqs')

    
    def put_messages(self, to_process: list[CommentData | PostData]):
        if not to_process:
            return
        
        messages = []
        for item in to_process:
            payload = {
                'type': type(item).__name__,
                'data': item.to_dict()
            }
            
            message = {
                'Id': str(uuid.uuid4()),
                'MessageBody': json.dumps(payload)
            }
            messages.append(message)
        
        batch_size = 10
        for i in range(0, len(messages), batch_size):
            batch = messages[i:i + batch_size]
            self._send_batch(batch)
    
    def _send_batch(self, batch: list[dict]):
        try:
            response = self.sqs_client.send_message_batch(
                QueueUrl=self.queue_url,
                Entries=batch
            )
            
            if 'Failed' in response and response['Failed']:
                for failed_msg in response['Failed']:
                    print(f"Failed to send message {failed_msg['Id']}: {failed_msg['Message']}")
            
            if 'Successful' in response:
                print(f"Successfully sent {len(response['Successful'])} messages")
                
        except ClientError as e:
            print(f"Error sending batch to SQS: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise

class PrintQueueFacade(SQSProcessingQueue, LoggingMixin):
    def put_messages(self, to_process: list[CommentData | PostData]):
        for item in to_process:
            print("Putting message")
            print(f"Type: {type(item).__name__}\nData: {item.to_dict()}\n")

    def connect_queue(self):
        return None

class CountQueueFacade(SQSProcessingQueue, LoggingMixin):
    def __init__(self):
        super().__init__()
        self.count = 0
        self.start_time = datetime.now()

    def put_messages(self, to_process: list[CommentData | PostData]):
        self.count += len(to_process)
        elapsed_time = (datetime.now() - self.start_time).total_seconds()
        print(f"\
        Total messages processed: {self.count}\n\
        Time Elapsed: {elapsed_time:.2f}s\
        Average Rate: {self.count / elapsed_time:.2f} messages/s \
        ")

    def connect_queue(self):
        return None

class ProdProducerApplication(SQSProcessingQueue, LoggingMixin):
    subreddits = ["wallstreetbets", "stocks", "Bogleheads"]
    def crawl_hot(self):
        self.log_info("Connecting to Queue")
        super().connect_queue()


        self.log_info("Starting Producer Application")
        while True:
            for subreddit in self.subreddits:
                reddit = SubredditFacade(subreddit)
                posts = reddit.get_hot_submissions(limit=5)
                to_process = []
                for post in posts:
                    post_data = PostData(post)
                    to_process.append(post_data)
                    
                    comments = reddit.get_all_comments_from_submission(post)
                    for comment in comments:
                        comment_data = CommentData(comment)
                        to_process.append(comment_data)
                if to_process:
                    super().put_messages(to_process)


class LocalTestProducerApplication(ProdProducerApplication, CountQueueFacade):
    'Prints messages that are produced'
    pass

class AppFactory(Config):
    def __init__(self):
        super().__init__()

    def create_app(self):
        if self.is_prod:
            return ProdProducerApplication()
        else:
            return LocalTestProducerApplication()


def main():
    app = AppFactory().create_app()
    app.crawl_hot()


if __name__ == "__main__":
    main()

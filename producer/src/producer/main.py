import random
from producer.utils import Config, LoggingMixin
from producer.reddit import FINANCE_SUBREDDITS, SubredditFacade, PostData, CommentData
from producer.queue import OutputAdapter, CountQueueFacade, ProcessingQueue


class ProducerApplication(OutputAdapter, LoggingMixin):
    def crawl_hot(self):
        super().log_info("Starting Producer Application")
        while True:
            next_subreddit = random.choice(FINANCE_SUBREDDITS)
            reddit = SubredditFacade(next_subreddit)
            posts = reddit.get_hot_submissions(limit=25)
            for post in posts:
                super().send(PostData(post).to_dict())
                comments = reddit.get_all_comments_from_submission(post)
                for comment in comments:
                    super().send(CommentData(comment).to_dict())
            super().log_info(f"Finished processing {next_subreddit}...")


class ProdProducerApplication(ProducerApplication, ProcessingQueue):
    "Production application that processes messages using SQS"


class LocalTestProducerApplication(ProducerApplication, CountQueueFacade):
    def __init__(self):
        super().__init__()
        self.connect_queue()
        super().log_info("Application initialized")
        super().log_info("Environment:")
        for attr, value in vars(self).items():
            super().log_info(f"{attr}: {value}")

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

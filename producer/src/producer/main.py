from producer.utils import Config, LoggingMixin
from producer.reddit import SubredditFacade, PostData, CommentData
from producer.queue import SQSProcessingQueue, CountQueueFacade

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
    "Prints messages that are produced"
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

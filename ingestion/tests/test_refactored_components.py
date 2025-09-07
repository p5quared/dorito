"""Tests demonstrating improved testability after refactoring"""

import pytest
from unittest.mock import Mock, patch
from praw.models import Comment

from shared.container import DIContainer
from shared.interfaces import ConfigProvider, Logger, RedditDataSink, DataProcessor
from shared.utils import Config
from shared.types import PostData
from producer.main import RedditScraperApplication, create_local_application
from producer.reddit import SubredditDataSource
from consumer.main import ConsumerApplication
from consumer.processor import FinancialRelevanceProcessor
from consumer.utils import CSVDataWriter


class TestConfig:
    """Test configuration provider functionality"""

    def test_config_with_env_override(self):
        """Test config with custom environment variables"""
        env_override = {
            "ENVIRONMENT": "prod",
            "REDDIT_CLIENT_ID": "test_id",
            "LOG_LEVEL": "DEBUG",
        }
        config = Config(env_override=env_override)

        assert config.is_prod is True
        assert config.reddit_client_id == "test_id"
        assert config.log_level == "DEBUG"

    def test_config_defaults(self):
        """Test config with default values"""
        config = Config(env_override={})

        assert config.is_prod is False
        assert config.aws_region == "us-east-2"
        assert config.log_level == "INFO"


class TestDependencyInjection:
    """Test dependency injection container"""

    def test_container_registration_and_retrieval(self):
        """Test basic DI container functionality"""
        container = DIContainer()

        # Register a singleton
        mock_logger = Mock(spec=Logger)
        container.register_singleton(Logger, mock_logger)

        # Register a factory
        def config_factory():
            return Config(env_override={"ENVIRONMENT": "test"})

        container.register_factory(ConfigProvider, config_factory)

        # Test retrieval
        retrieved_logger = container.get(Logger)
        retrieved_config = container.get(ConfigProvider)

        assert retrieved_logger is mock_logger
        assert isinstance(retrieved_config, Config)
        assert retrieved_config.is_prod is False

    def test_container_service_not_found(self):
        """Test container raises error for unregistered services"""
        container = DIContainer()

        with pytest.raises(ValueError, match="Service not registered"):
            container.get(Logger)


class TestRedditDataSource:
    """Test Reddit data source with mocked dependencies"""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for testing"""
        mock_reddit_client = Mock()
        mock_logger = Mock(spec=Logger)

        # Mock Reddit API responses
        mock_submission = Mock()
        mock_submission.id = "test_post_1"
        mock_submission.title = "Test Post"
        mock_submission.selftext = "Test post body"
        mock_submission.score = 10
        mock_submission.subreddit.display_name = "test"

        # Create mock that will pass isinstance check
        mock_comment = Mock()
        mock_comment.id = "test_comment_1"
        mock_comment.body = "Test comment"
        mock_comment.score = 5
        mock_comment.submission.id = "test_post_1"
        mock_comment.parent_id = "test_post_1"
        mock_comment.subreddit.display_name = "test"
        # Make isinstance(mock_comment, Comment) return True
        mock_comment.__class__ = Comment

        mock_reddit_client.reddit.subreddit.return_value.hot.return_value = [
            mock_submission
        ]
        # Mock comment list method properly
        mock_comment_list = Mock()
        mock_comment_list.list.return_value = [mock_comment]
        mock_submission.comments = mock_comment_list

        return {
            "reddit_client": mock_reddit_client,
            "logger": mock_logger,
            "submission": mock_submission,
            "comment": mock_comment,
        }

    def test_subreddit_data_source_get_content(self, mock_dependencies):
        """Test getting content from subreddit"""
        data_source = SubredditDataSource(
            "test", mock_dependencies["reddit_client"], mock_dependencies["logger"]
        )

        content = list(data_source.get_content(limit=5))

        assert len(content) == 1
        assert content[0] is mock_dependencies["submission"]
        mock_dependencies["logger"].info.assert_called()

    def test_subreddit_data_source_get_comments(self, mock_dependencies):
        """Test getting comments from submission"""
        data_source = SubredditDataSource(
            "test", mock_dependencies["reddit_client"], mock_dependencies["logger"]
        )

        # First setup the submission mock properly
        submission = mock_dependencies["submission"]
        submission.comments.replace_more = Mock()
        # Ensure the list method returns our mock comment
        submission.comments.list.return_value = [mock_dependencies["comment"]]

        comments = data_source.get_comments_from_submission(submission)

        assert len(comments) == 1
        assert comments[0] is mock_dependencies["comment"]
        mock_dependencies["logger"].info.assert_called()


class TestRedditScraperApplication:
    """Test producer application with dependency injection"""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for producer testing"""
        mock_message_sink = Mock(spec=RedditDataSink)
        mock_reddit_client = Mock()
        mock_logger = Mock(spec=Logger)

        # Mock submission and comment
        mock_submission = Mock()
        mock_submission.id = "test_post_1"
        mock_submission.title = "Test Post"
        mock_submission.selftext = "Test post body"
        mock_submission.score = 10
        mock_submission.subreddit.display_name = "test"

        mock_comment = Mock()
        mock_comment.id = "test_comment_1"
        mock_comment.body = "Test comment"
        mock_comment.score = 5
        mock_comment.submission.id = "test_post_1"
        mock_comment.parent_id = "test_post_1"
        mock_comment.subreddit.display_name = "test"

        return {
            "message_sink": mock_message_sink,
            "reddit_client": mock_reddit_client,
            "logger": mock_logger,
            "submission": mock_submission,
            "comment": mock_comment,
        }

    def test_scraper_application_initialization(self, mock_dependencies):
        """Test scraper application can be initialized with dependencies"""
        app = RedditScraperApplication(
            mock_dependencies["message_sink"],
            mock_dependencies["reddit_client"],
            mock_dependencies["logger"],
            subreddits=["test"],
        )

        assert app._message_sink is mock_dependencies["message_sink"]
        assert app._reddit_client is mock_dependencies["reddit_client"]
        assert app._logger is mock_dependencies["logger"]
        assert app._subreddits == ["test"]

    @patch("producer.main.SubredditDataSource")
    def test_scraper_processes_content(self, mock_data_source_class, mock_dependencies):
        """Test that scraper processes posts and comments"""
        # Setup mock data source
        mock_data_source = Mock()
        mock_data_source.get_content.return_value = [mock_dependencies["submission"]]
        mock_data_source.get_comments_from_submission.return_value = [
            mock_dependencies["comment"]
        ]
        mock_data_source_class.return_value = mock_data_source

        app = RedditScraperApplication(
            mock_dependencies["message_sink"],
            mock_dependencies["reddit_client"],
            mock_dependencies["logger"],
            subreddits=["test"],
        )

        app._loop()

        # Verify message sink was called for both post and comment
        assert mock_dependencies["message_sink"].send_message.call_count == 2
        mock_dependencies["logger"].info.assert_called()


class TestFinancialRelevanceProcessor:
    """Test financial relevance processor"""

    @pytest.fixture
    def mock_processor_dependencies(self):
        """Create mock dependencies for processor testing"""
        mock_logger = Mock(spec=Logger)

        # Mock the tokenizer and model
        with patch("consumer.processor.AutoTokenizer") as mock_tokenizer_class:
            with patch(
                "consumer.processor.AutoModelForSequenceClassification"
            ) as mock_model_class:
                mock_tokenizer = Mock()
                mock_model = Mock()

                mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
                mock_model_class.from_pretrained.return_value = mock_model

                # Mock model outputs
                mock_outputs = Mock()
                mock_outputs.logits = Mock()
                mock_model.return_value = mock_outputs

                processor = FinancialRelevanceProcessor(mock_logger)
                # Store references for easier access in tests
                processor.outputs = mock_outputs

                return {
                    "processor": processor,
                    "logger": mock_logger,
                    "tokenizer": mock_tokenizer,
                    "model": mock_model,
                    "outputs": mock_outputs,
                }

    def test_processor_initialization(self, mock_processor_dependencies):
        """Test processor initialization with custom parameters"""
        processor = mock_processor_dependencies["processor"]
        logger = mock_processor_dependencies["logger"]

        assert processor._logger is logger
        assert processor._threshold == 0.5
        logger.info.assert_called_once()

    def test_processor_handles_empty_content(self, mock_processor_dependencies):
        """Test processor handles empty content gracefully"""
        processor = mock_processor_dependencies["processor"]

        post_data = PostData(
            id="test",
            subreddit="test",
            title="Test",
            body="",  # Empty body
            score=1,
        )

        result = processor.process(post_data)

        assert result == {}
        mock_processor_dependencies["logger"].debug.assert_called()

    @patch("consumer.processor.torch.nn.functional.softmax")
    @patch.object(FinancialRelevanceProcessor, "_is_financially_relevant")
    def test_processor_filters_non_financial_content(
        self, mock_is_financial, mock_softmax, mock_processor_dependencies
    ):
        """Test processor filters out non-financial content"""
        processor = mock_processor_dependencies["processor"]

        # Mock that content is not financially relevant
        mock_is_financial.return_value = False

        post_data = PostData(
            id="test",
            subreddit="test",
            title="Test",
            body="This is about cats",
            score=1,
        )

        result = processor.process(post_data)

        assert result == {}
        mock_processor_dependencies["logger"].debug.assert_called()

    @patch("consumer.processor.torch.nn.functional.softmax")
    @patch.object(FinancialRelevanceProcessor, "_is_financially_relevant")
    def test_processor_accepts_financial_content(
        self, mock_is_financial, mock_softmax, mock_processor_dependencies
    ):
        """Test processor accepts financial content"""
        processor = mock_processor_dependencies["processor"]

        # Mock that content is financially relevant
        mock_is_financial.return_value = True

        post_data = PostData(
            id="test",
            subreddit="test",
            title="Test",
            body="Stock market analysis",
            score=1,
        )

        result = processor.process(post_data)

        assert result != {}
        assert result["id"] == "test"
        assert result["body"] == "Stock market analysis"


class TestCSVDataWriter:
    """Test CSV data writer functionality"""

    @pytest.fixture
    def temp_csv_file(self, tmp_path):
        """Create temporary CSV file for testing"""
        return tmp_path / "test_data.csv"

    def test_csv_writer_initialization(self, temp_csv_file):
        """Test CSV writer initialization"""
        writer = CSVDataWriter(
            str(temp_csv_file), fieldnames=["id", "body", "score"]
        )

        assert writer._filename == str(temp_csv_file)
        assert writer._fieldnames == ["id", "body", "score"]
        assert writer._header_written == False

    def test_csv_writer_writes_immediately(self, temp_csv_file):
        """Test CSV writer writes data immediately"""
        writer = CSVDataWriter(
            str(temp_csv_file), fieldnames=["id", "body", "score"]
        )

        # Write one item - should write immediately
        writer.write({"id": "1", "body": "test", "score": 10})
        assert temp_csv_file.exists()
        assert writer._header_written == True

        # Write second item - should append to file
        writer.write({"id": "2", "body": "test2", "score": 20})
        
        # Check file contents
        content = temp_csv_file.read_text()
        lines = content.strip().split("\n")
        assert len(lines) == 3  # header + 2 data rows

    def test_csv_writer_cleans_text(self, temp_csv_file):
        """Test CSV writer cleans text properly"""
        writer = CSVDataWriter(
            str(temp_csv_file), fieldnames=["id", "body"]
        )

        writer.write({"id": "1", "body": "text\nwith\rnewlines,and,commas"})

        content = temp_csv_file.read_text()
        assert "text with newlines and commas" in content
        assert "\n" not in content.split("\n")[1]  # Not in data row

    def test_csv_writer_skips_empty_data(self, temp_csv_file):
        """Test CSV writer skips empty data"""
        writer = CSVDataWriter(
            str(temp_csv_file), fieldnames=["id", "body"]
        )

        writer.write({})  # Empty dict
        writer.write(None)  # None value

        assert not temp_csv_file.exists()


class TestConsumerApplication:
    """Test consumer application with dependency injection"""

    @pytest.fixture
    def mock_consumer_dependencies(self):
        """Create mock dependencies for consumer testing"""
        mock_message_source = Mock()
        mock_processor = Mock(spec=DataProcessor)
        mock_writer = Mock()
        mock_logger = Mock(spec=Logger)

        return {
            "message_source": mock_message_source,
            "processor": mock_processor,
            "writer": mock_writer,
            "logger": mock_logger,
        }

    def test_consumer_application_initialization(self, mock_consumer_dependencies):
        """Test consumer application initialization"""
        app = ConsumerApplication(
            mock_consumer_dependencies["message_source"],
            mock_consumer_dependencies["processor"],
            mock_consumer_dependencies["writer"],
            mock_consumer_dependencies["logger"],
        )

        assert app._message_source is mock_consumer_dependencies["message_source"]
        assert app._processor is mock_consumer_dependencies["processor"]
        assert app._writer is mock_consumer_dependencies["writer"]
        assert app._logger is mock_consumer_dependencies["logger"]

    @patch("consumer.main.deserialize_reddit_data")
    def test_consumer_processes_messages(
        self, mock_deserialize, mock_consumer_dependencies
    ):
        """Test consumer processes messages correctly"""
        # Setup mocks
        mock_data = Mock()
        mock_deserialize.return_value = mock_data

        mock_message = {"Body": '{"test": "data"}'}
        mock_consumer_dependencies["message_source"].messages = [mock_message]
        mock_consumer_dependencies["processor"].process.return_value = {
            "processed": "data"
        }

        app = ConsumerApplication(**mock_consumer_dependencies)

        # Run one iteration
        try:
            app._loop()
        except StopIteration:
            pass  # Expected when mock iterator is exhausted

        # Verify processing chain
        mock_deserialize.assert_called_with('{"test": "data"}')
        mock_consumer_dependencies["processor"].process.assert_called_with(mock_data)
        mock_consumer_dependencies["writer"].write.assert_called_with(
            {"processed": "data"}
        )
        mock_consumer_dependencies["message_source"].delete_message.assert_called_with(
            mock_message
        )

    def test_consumer_handles_processing_errors(self, mock_consumer_dependencies):
        """Test consumer handles processing errors gracefully"""
        mock_message = {"Body": "invalid json"}
        mock_consumer_dependencies["message_source"].messages = [mock_message]

        app = ConsumerApplication(**mock_consumer_dependencies)

        # Should not raise exception, but should log error and delete message
        try:
            app._loop()
        except StopIteration:
            pass

        mock_consumer_dependencies["logger"].error.assert_called()
        mock_consumer_dependencies["message_source"].delete_message.assert_called_with(
            mock_message
        )


class TestIntegration:
    """Integration tests using the DI container"""

    def test_create_local_application_integration(self):
        """Test creating a local application through the DI container"""
        from shared.container import create_container

        container = create_container()

        # Override config for testing
        test_config = Config(env_override={"ENVIRONMENT": "dev"})
        container.register_singleton(ConfigProvider, test_config)

        app = create_local_application(container)

        assert isinstance(app, RedditScraperApplication)
        assert app._logger is not None
        assert app._message_sink is not None
        assert app._reddit_client is not None

    @patch("consumer.processor.AutoTokenizer")
    @patch("consumer.processor.AutoModelForSequenceClassification")
    def test_consumer_factory_integration(self, mock_model_class, mock_tokenizer_class):
        """Test creating consumer through factory with DI container"""
        from consumer.main import create_local_consumer
        from shared.container import create_container

        # Mock ML model dependencies
        mock_tokenizer_class.from_pretrained.return_value = Mock()
        mock_model_class.from_pretrained.return_value = Mock()

        container = create_container()

        # Override config for testing
        test_config = Config(
            env_override={"ENVIRONMENT": "dev", "SQS_QUEUE_URL": "test-queue"}
        )
        container.register_singleton(ConfigProvider, test_config)

        app = create_local_consumer(container)

        assert isinstance(app, ConsumerApplication)
        assert app._logger is not None
        assert app._message_source is not None
        assert app._processor is not None
        assert app._writer is not None

"""Legacy test file - main tests are now in test_refactored_components.py and test_error_handling.py"""

import pytest
from shared.types import (
    PostData,
    CommentData,
    get_post_comment_csv_columns,
    deserialize_reddit_data,
)
from unittest.mock import Mock


def test_legacy_placeholder():
    """Placeholder test to ensure pytest runs"""
    assert True


class TestDataTypes:
    """Test data type functionality"""

    def test_post_data_creation(self):
        """Test PostData creation and serialization"""
        post = PostData(
            id="test_123",
            subreddit="test_sub",
            title="Test Title",
            body="Test body content",
            score=42,
        )

        assert post.id == "test_123"
        assert post.message_t == "post"
        assert post.score == 42

    def test_comment_data_creation(self):
        """Test CommentData creation and serialization"""
        comment = CommentData(
            id="comment_123",
            subreddit="test_sub",
            body="Test comment",
            score=5,
            submission_id="post_123",
            parent_id="post_123",
        )

        assert comment.id == "comment_123"
        assert comment.message_t == "comment"
        assert comment.submission_id == "post_123"

    def test_post_data_from_submission(self):
        """Test creating PostData from Reddit submission"""
        mock_submission = Mock()
        mock_submission.id = "reddit_post_123"
        mock_submission.title = "Reddit Post Title"
        mock_submission.selftext = "Reddit post content"
        mock_submission.score = 100
        mock_submission.subreddit.display_name = "stocks"

        post = PostData.from_submission(mock_submission)

        assert post.id == "reddit_post_123"
        assert post.title == "Reddit Post Title"
        assert post.body == "Reddit post content"
        assert post.subreddit == "stocks"
        assert post.score == 100

    def test_comment_data_from_comment(self):
        """Test creating CommentData from Reddit comment"""
        mock_comment = Mock()
        mock_comment.id = "reddit_comment_123"
        mock_comment.body = "Great analysis!"
        mock_comment.score = 25
        mock_comment.submission.id = "parent_post_123"
        mock_comment.parent_id = "parent_post_123"
        mock_comment.subreddit.display_name = "investing"

        comment = CommentData.from_comment(mock_comment)

        assert comment.id == "reddit_comment_123"
        assert comment.body == "Great analysis!"
        assert comment.score == 25
        assert comment.submission_id == "parent_post_123"
        assert comment.subreddit == "investing"

    def test_get_csv_columns(self):
        """Test CSV column generation"""
        columns = get_post_comment_csv_columns()

        # Should contain fields from both PostData and CommentData
        assert "id" in columns
        assert "subreddit" in columns
        assert "body" in columns
        assert "score" in columns
        assert "message_t" in columns
        assert "title" in columns  # Post-specific
        assert "submission_id" in columns  # Comment-specific
        assert "parent_id" in columns  # Comment-specific

        # Should be sorted
        assert columns == sorted(columns)

    def test_deserialize_post_data(self):
        """Test deserializing post data from JSON"""
        json_str = '{"id": "test_post", "subreddit": "test", "title": "Test", "body": "content", "score": 10, "message_t": "post"}'

        data = deserialize_reddit_data(json_str)

        assert isinstance(data, PostData)
        assert data.id == "test_post"
        assert data.title == "Test"
        assert data.message_t == "post"

    def test_deserialize_comment_data(self):
        """Test deserializing comment data from JSON"""
        json_str = '{"id": "test_comment", "subreddit": "test", "body": "comment", "score": 5, "submission_id": "post_123", "parent_id": "post_123", "message_t": "comment"}'

        data = deserialize_reddit_data(json_str)

        assert isinstance(data, CommentData)
        assert data.id == "test_comment"
        assert data.body == "comment"
        assert data.message_t == "comment"
        assert data.submission_id == "post_123"

    def test_deserialize_unknown_type(self):
        """Test deserializing unknown message type raises error"""
        json_str = '{"message_t": "unknown_type", "data": "value"}'

        with pytest.raises(ValueError, match="Unknown message type"):
            deserialize_reddit_data(json_str)

    def test_data_serialization_roundtrip(self):
        """Test data can be serialized and deserialized correctly"""
        original_post = PostData(
            id="roundtrip_test",
            subreddit="test",
            title="Roundtrip Test",
            body="Testing serialization",
            score=99,
        )

        # Serialize to JSON
        json_str = original_post.to_json()

        # Deserialize back
        deserialized_post = deserialize_reddit_data(json_str)

        assert isinstance(deserialized_post, PostData)
        assert deserialized_post.id == original_post.id
        assert deserialized_post.title == original_post.title
        assert deserialized_post.body == original_post.body
        assert deserialized_post.score == original_post.score
        assert deserialized_post.message_t == original_post.message_t

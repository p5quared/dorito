import pytest
from producer.reddit import SubredditFacade

THE_GOOD_WORD = "BANANA"


@pytest.fixture
def mock_reddit(mocker):
    mock_reddit_class = mocker.patch("praw.Reddit")
    mock_client = mocker.MagicMock()
    mock_reddit_class.return_value = mock_client

    mock_submission = mocker.MagicMock()
    mock_client.subreddit.return_value.hot.return_value = [mock_submission] * 100
    mock_submission.comments.list.return_value = [THE_GOOD_WORD]
    return mock_client


@pytest.fixture
def subreddit_facade():
    return SubredditFacade(THE_GOOD_WORD)


def test_getHot_uses_correct_params(mock_reddit, subreddit_facade):
    limit = 25
    sl = subreddit_facade.get_hot_submissions(limit)

    # Calls subreddit with the correct subreddit name
    mock_reddit.subreddit.assert_called_once_with(THE_GOOD_WORD)

    # Calls hot with the correct limit
    mock_reddit.subreddit.return_value.hot.assert_called_once_with(limit=limit)

    # Checks that the returned list has the correct length
    # This might be redundant
    assert len(list(sl)) == limit


def test_getAllCommentsFromSubmission(mock_reddit, subreddit_facade):
    sl = subreddit_facade.get_hot_submissions(1)
    submission = next(sl)

    subreddit_facade.get_all_comments_from_submission(submission)

    # All comments were replaced
    mock_reddit.subreddit.return_value.hot.return_value[
        0
    ].comments.replace_more.assert_called_once_with(limit=None)

    # The comments list was called
    mock_reddit.subreddit.return_value.hot.return_value[
        0
    ].comments.list.assert_called_once()

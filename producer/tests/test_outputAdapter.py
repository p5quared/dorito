import pytest
from producer.queue import ProcessingQueue


@pytest.fixture
def mock_sqs(mocker):
    mock_sqs_class = mocker.patch("boto3.client")
    mock_client = mocker.MagicMock()
    mock_sqs_class.return_value = mock_client
    return mock_client


def test_RedditProcessingQueueSendsMessage(mock_sqs):
    q = ProcessingQueue()
    q.connect_queue()
    q.send({"key": "value"})

    mock_sqs.send_message.assert_called_once_with(
        QueueUrl="MISSING QUEUE URL",
        MessageBody=str({"key": "value"}),
    )

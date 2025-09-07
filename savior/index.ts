import { SQSEvent, SQSBatchResponse, SQSBatchItemFailure } from 'aws-lambda';

export const handler = async (event: SQSEvent): Promise<SQSBatchResponse> => {
  const batchItemFailures: SQSBatchItemFailure[] = [];

  for (const record of event.Records) {
    try {
      console.log('Processing SQS message:', record.messageId);
      
      // Parse SNS message from SQS body
      const snsMessage = JSON.parse(record.body);
      
      if (snsMessage.Type === 'Notification') {
        console.log('SNS Topic ARN:', snsMessage.TopicArn);
        console.log('SNS Message ID:', snsMessage.MessageId);
        console.log('SNS Subject:', snsMessage.Subject);
        
        // The actual message payload is in the Message field
        const messagePayload = snsMessage.Message;
        console.log('Message payload:', messagePayload);
        
        await handleMessage(messagePayload);
      } else {
        console.warn('Received non-notification SNS message type:', snsMessage.Type);
      }
      
    } catch (error) {
      console.error(`Failed to process message ${record.messageId}:`, error);
      batchItemFailures.push({
        itemIdentifier: record.messageId
      });
    }
  }

  return {
    batchItemFailures
  };
};

const handleMessage = async (message: any) => {
  console.log('Handling message:', message);
}

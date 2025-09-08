import { SQSEvent, SQSBatchResponse, SQSBatchItemFailure } from 'aws-lambda';
import { RedditDataProducedEvent, SourceType, validateRedditDataProducedEvent } from './types';
import { RawDataEntity } from './ddb';
import { PutItemCommand } from 'dynamodb-toolbox';

export const handler = async (event: SQSEvent): Promise<SQSBatchResponse> => {
  console.log(`Received ${event.Records.length} records`);

  const batchItemFailures: SQSBatchItemFailure[] = [];

  for (const record of event.Records) {
	console.log('Processing SQS message:', record.messageId);
    try {
      const dataProducedMessage = JSON.parse(record.body);
      
	  const isRedditDataProducedEvent = validateRedditDataProducedEvent(dataProducedMessage)
      if (isRedditDataProducedEvent) {
        await handleRedditDataProduced(dataProducedMessage);
      } else {
		throw new Error('Unrecognized record type');
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

const handleRedditDataProduced = async (dataProduced: RedditDataProducedEvent) => {
  const r = await RawDataEntity.build(PutItemCommand)
  .item({
	id: dataProduced.data.id,
	sourceType: SourceType.REDDIT,
	sourceDate: dataProduced.meta.source_date,
	data: dataProduced.data
  }).options({ returnValues: 'ALL_OLD'}).send()
  return r
}

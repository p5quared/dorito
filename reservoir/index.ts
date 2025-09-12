import { saveRedditDataDDB } from './ddb';
import { RawDataProducedEvent, validateRawDataProducedEvent } from './parser';
import { eventHandler, MessageHandlerBuilder } from './handling';
import { getConfigRequired, printMessage } from './utils';
import { SQSHandler } from 'aws-lambda';
import { SNSStrategyBuilder } from './publisher';


const RedditDataPublisher = new SNSStrategyBuilder<RawDataProducedEvent>()
	.withSnsTopicArn(getConfigRequired('SNS_TOPIC_ARN'))
	.withEventType("trawl.reddit")
	.withAwsRegion(getConfigRequired('AWS_REGION'))
	.withCorrelationIdResolver((redditData) => redditData.meta.correlation_id)
	.build();


const RedditRecordHandler = new MessageHandlerBuilder<RawDataProducedEvent>()
	.withValidator(validateRawDataProducedEvent)
	.withHandler(saveRedditDataDDB)
	.withHandler(printMessage)
	.withPublisher(RedditDataPublisher.publishData.bind(RedditDataPublisher))
	.build()

const RedditEventHandler = eventHandler<RawDataProducedEvent>(RedditRecordHandler.handle.bind(RedditRecordHandler))

export const handler: SQSHandler = RedditEventHandler

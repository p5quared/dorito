import { saveRedditDataDDB } from './ddb';
import { RawDataProducedEvent, validateRawDataProducedEvent } from './parser';
import { eventHandler, MessageHandlerBuilder } from './handling';
import { getConfigRequired, printMessage } from './utils';
import { SQSHandler } from 'aws-lambda';
import { SNSStrategyBuilder } from './publisher';


const RawDataPublisher = new SNSStrategyBuilder<RawDataProducedEvent>()
	.withSnsTopicArn(getConfigRequired('SNS_TOPIC_ARN'))
	.withEventType("trawl.raw")
	.withAwsRegion(getConfigRequired('AWS_REGION'))
	.withCorrelationIdResolver((redditData) => redditData.meta.correlation_id)
	.build();


const RawDataRecordHandler = new MessageHandlerBuilder<RawDataProducedEvent>()
	.withValidator(validateRawDataProducedEvent)
	.withHandler(saveRedditDataDDB)
	.withHandler(printMessage)
	.withPublisher(RawDataPublisher.publishData.bind(RawDataPublisher))
	.build()

const RawDataEventHandler = eventHandler<RawDataProducedEvent>(RawDataRecordHandler.handle.bind(RawDataRecordHandler))

export const handler: SQSHandler = RawDataEventHandler

import { SQSHandler } from "aws-lambda";
import { eventHandler, MessageHandlerBuilder } from "./handling";
import { KeywordProducedEvent, validateKeywordProducedEvent } from "./parser";
import { SNSStrategyBuilder } from "./publisher";
import { printMessage } from "./utils";

const KeywordPublisher = new SNSStrategyBuilder<KeywordProducedEvent>()
	.withSnsTopicArn(process.env.SNS_TOPIC_ARN!)
	.withEventType("reservoir.keyword")
	.withAwsRegion(process.env.AWS_REGION!)
	.withCorrelationIdResolver((keywordData) => keywordData.meta.correlation_id)
	.build();

const KeywordRecordHandler = new MessageHandlerBuilder<KeywordProducedEvent>()
	.withValidator(validateKeywordProducedEvent) // TODO: Implement validation
	.withHandler(printMessage)
	.withPublisher(KeywordPublisher.publishData.bind(KeywordPublisher))
	.build()


const KeywordEventHandler = eventHandler<KeywordProducedEvent>(KeywordRecordHandler.handle.bind(KeywordRecordHandler))

export const handler: SQSHandler = KeywordEventHandler

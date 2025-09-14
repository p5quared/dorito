import { SQSHandler } from "aws-lambda";
import { eventHandler, MessageHandlerBuilder } from "./handling";
import { KeywordProducedEvent, validateKeywordProducedEvent } from "./parser";
import { SNSStrategyBuilder } from "./publisher";
import { getConfigRequired, printMessage } from "./utils";

const KeywordPublisher = new SNSStrategyBuilder<KeywordProducedEvent>()
	.withSnsTopicArn(getConfigRequired('OUTPUT_SNS_TOPIC_ARN'))
	.withEventType("reservoir.keyword")
	.withAwsRegion(getConfigRequired('AWS_REGION'))
	.build();

const KeywordRecordHandler = new MessageHandlerBuilder<KeywordProducedEvent>()
	.withValidator(validateKeywordProducedEvent)
	.withHandler(printMessage)
	.withPublisher(KeywordPublisher.publishData.bind(KeywordPublisher))
	.build()


const KeywordEventHandler = eventHandler<KeywordProducedEvent>(KeywordRecordHandler.handle.bind(KeywordRecordHandler))

export const handler: SQSHandler = KeywordEventHandler

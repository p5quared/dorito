import { PublishCommand, SNSClient } from "@aws-sdk/client-sns";
import { EventMetadata, EventType, RawDataProducedEvent } from "./parser";

interface SNSEnvelope {
	data: any;
	meta: EventMetadata

}

interface DataSavedEvent<T> extends SNSEnvelope {
	data: T;
}

export class NullPublisher {
	async publish(any: any) {
		Promise.resolve()
	}
}


type CorrelationIdResolver<T> = (i: T) => string

export class SNSStrategy<T> {
	private readonly sns_client: SNSClient
	private readonly sns_topic_arn: string
	private readonly event_type: EventType
	private readonly correlation_id_resolver: CorrelationIdResolver<T>

	constructor(
		sns_topic_arn: string,
		event_type: EventType,
		aws_region: string,
		correlation_id_resolver: CorrelationIdResolver<T>
	) {
		this.event_type = event_type;
		this.sns_topic_arn = sns_topic_arn;
		this.sns_client = new SNSClient({ region: aws_region });
		this.correlation_id_resolver = correlation_id_resolver;
	}

	async publishData(data: T) {
		const message = this.buildEnvelope(data);

		await this.sns_client.send(new PublishCommand({
			TopicArn: this.sns_topic_arn,
			Message: JSON.stringify(message),
			Subject: this.event_type,
		})
		)
	}

	private buildEnvelope(data: T): DataSavedEvent<T> {
		return {
			data,
			meta: {
				correlation_id: this.correlation_id_resolver(data),
				source_date: new Date().toISOString(),
				event_type: this.event_type,

			}
		}
	}
}

export class SNSStrategyBuilder<T> {
	private sns_topic_arn!: string;
	private event_type!: EventType;
	private aws_region!: string;
	private correlation_id_resolver!: CorrelationIdResolver<T>;

	withSnsTopicArn(sns_topic_arn: string): SNSStrategyBuilder<T> {
		this.sns_topic_arn = sns_topic_arn;
		return this;
	}

	withEventType(event_type: EventType): SNSStrategyBuilder<T> {
		this.event_type = event_type;
		return this;
	}

	withAwsRegion(aws_region: string): SNSStrategyBuilder<T> {
		this.aws_region = aws_region;
		return this;
	}

	withCorrelationIdResolver(correlation_id_resolver: CorrelationIdResolver<T>): SNSStrategyBuilder<T> {
		this.correlation_id_resolver = correlation_id_resolver;
		return this;
	}

	build(): SNSStrategy<T> {
		if (!this.sns_topic_arn) {
			throw new Error("SNS Topic ARN is required");
		}
		if (!this.event_type) {
			throw new Error("Event Type is required");
		}
		if (!this.aws_region) {
			throw new Error("AWS Region is required");
		}
		return new SNSStrategy(this.sns_topic_arn, this.event_type, this.aws_region, this.correlation_id_resolver);
	}
}

export function createRedditDataSavedEventPublisher(
	snsTopicArn: string,
	awsRegion: string
): SNSStrategy<RawDataProducedEvent['data']> {
	return new SNSStrategyBuilder<RawDataProducedEvent['data']>()
		.withSnsTopicArn(snsTopicArn)
		.withEventType("reservoir.raw")
		.withAwsRegion(awsRegion)
		.withCorrelationIdResolver((redditData) => redditData.id)
		.build();
}

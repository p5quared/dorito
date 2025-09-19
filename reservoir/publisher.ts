import { PublishCommand, SNSClient } from "@aws-sdk/client-sns";
import { EventType } from "./parser";
import { getConfigRequired } from "./utils";

export class SNSStrategy<T> {
	private readonly sns_client: SNSClient
	private readonly sns_topic_arn: string
	private readonly event_type: EventType

	constructor(
		sns_topic_arn: string,
		event_type: EventType,
		aws_region: string,
	) {
		this.event_type = event_type;
		this.sns_topic_arn = sns_topic_arn;
		this.sns_client = new SNSClient({ region: aws_region });
	}

	async publishData(data: T) {
		await this.sns_client.send(new PublishCommand({
			TopicArn: this.sns_topic_arn,
			Message: JSON.stringify(data),
			MessageAttributes: {
				eventType: {
					DataType: "String",
					StringValue: this.event_type,
				}
			},
		})
		)
	}
}

export class SNSStrategyBuilder<T> {
	private sns_topic_arn!: string;
	private event_type!: EventType;
	private aws_region!: string;

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
		return new SNSStrategy(this.sns_topic_arn, this.event_type, this.aws_region);
	}
}

export const publishKeyword = async (keyword: string) => {
  const KeywordPublisher = new SNSStrategyBuilder<{ keyword: string }>()
  .withSnsTopicArn(getConfigRequired('OUTPUT_SNS_TOPIC_ARN'))
  .withEventType("reservoir.keyword")
  .withAwsRegion(getConfigRequired('AWS_REGION'))
  .build();

  await KeywordPublisher.publishData({ keyword });
}

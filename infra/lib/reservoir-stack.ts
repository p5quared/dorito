import { CfnOutput, Duration, RemovalPolicy, Stack, StackProps } from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as lambdaEventSources from 'aws-cdk-lib/aws-lambda-event-sources';
import * as sqs from 'aws-cdk-lib/aws-sqs';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as snsSubscriptions from 'aws-cdk-lib/aws-sns-subscriptions';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as nodejs from 'aws-cdk-lib/aws-lambda-nodejs';
import { Construct } from 'constructs';

interface ReservoirStackProps extends StackProps {
	vpc: ec2.Vpc
}

export class ReservoirStack extends Stack {
	private readonly table: dynamodb.Table;
	public readonly snsTopic: sns.Topic;

	constructor(scope: Construct, id: string, props: ReservoirStackProps) {
		super(scope, id, props);

		this.table = new dynamodb.Table(this, 'DDBTable', {
			tableName: 'Reservoir',
			partitionKey: {
				name: 'PK', type: dynamodb.AttributeType.STRING
			},
			sortKey: {
				name: 'SK', type: dynamodb.AttributeType.STRING
			},
			billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
			removalPolicy: RemovalPolicy.DESTROY,
		});

		this.snsTopic = new sns.Topic(this, 'ReservoirTopic', {
			topicName: 'ReservoirTopic',
		})

		new CfnOutput(this, 'SNSTopicArn', {
			value: this.snsTopic.topicArn,
			description: 'Reservoir SNS Topic ARN',
			exportName: `${id}-SNS-Topic-ARN`,
		});

		new CfnOutput(this, 'DDBTableName', {
			value: this.table.tableName,
			description: 'Reservoir DynamoDB Table Name',
			exportName: `${id}-DDB-Table-Name`,
		});

		new CfnOutput(this, 'DDBTableArn', {
			value: this.table.tableArn,
			description: 'Reservoir DynamoDB Table ARN',
			exportName: `${id}-DDB-Table-ARN`,
		});
	}

	// Filter example from AWS docs
	//// Lambda should receive only message matching the following conditions on attributes:
	// color: 'red' or 'orange' or begins with 'bl'
	// size: anything but 'small' or 'medium'
	// price: between 100 and 200 or greater than 300
	// store: attribute must be present
	//
	// myTopic.addSubscription(new subscriptions.LambdaSubscription(fn, {
	//   filterPolicy: {
	//     color: sns.SubscriptionFilter.stringFilter({
	//       allowlist: ['red', 'orange'],
	//       matchPrefixes: ['bl'],
	//       matchSuffixes: ['ue'],
	//     }),
	//     size: sns.SubscriptionFilter.stringFilter({
	//       denylist: ['small', 'medium'],
	//     }),
	//     price: sns.SubscriptionFilter.numericFilter({
	//       between: { start: 100, stop: 200 },
	//       greaterThan: 300,
	//     }),
	//     store: sns.SubscriptionFilter.existsFilter(),
	//   },
	//
	persist_topic(
		inputTopic: sns.Topic,
		handlerLocation: string,
		uniqueId: string,
	) {
		const lambdaFunction = new nodejs.NodejsFunction(this, `${uniqueId}-Lambda`, {
			entry: handlerLocation,
			timeout: Duration.seconds(10),
			memorySize: 128,
			environment: {
				DYNAMODB_TABLE_NAME: this.table.tableName,
				OUTPUT_SNS_TOPIC_ARN: this.snsTopic.topicArn,
			},
			runtime: lambda.Runtime.NODEJS_LATEST,
		});

		const dlq = new sqs.Queue(this, `${uniqueId}-DLQ`, {
			retentionPeriod: Duration.days(14),
		});

		const inputQueue = new sqs.Queue(this, `${uniqueId}-Queue`, {
			visibilityTimeout: Duration.minutes(1),
			retentionPeriod: Duration.days(14),
			deadLetterQueue: {
				queue: dlq,
				maxReceiveCount: 1,
			},
		});

		inputQueue.grantConsumeMessages(lambdaFunction);
		this.table.grantWriteData(lambdaFunction);
		this.snsTopic.grantPublish(lambdaFunction);

		lambdaFunction.addEventSource(
			new lambdaEventSources.SqsEventSource(inputQueue, {
				batchSize: 100,
				maxBatchingWindow: Duration.seconds(10),
			})
		);

		inputTopic.addSubscription(
			new snsSubscriptions.SqsSubscription(inputQueue, {
				rawMessageDelivery: true,
			})
		);
		console.log(`Topic ${inputTopic.topicArn} is being persisted by ${lambdaFunction.functionName}`)

		return uniqueId;
	}

	private createGeneralHandlingQueue(uniqueId: string) {
		const dlq = new sqs.Queue(this, `${uniqueId}-DLQ`, {
			retentionPeriod: Duration.days(14),
		});

		return new sqs.Queue(this, `${uniqueId}-Queue`, {
			visibilityTimeout: Duration.minutes(1),
			retentionPeriod: Duration.days(14),
			deadLetterQueue: {
				queue: dlq,
				maxReceiveCount: 3,
			},
		});
	}

	newPersistenceQueue(
		handlerLocation: string,
		uniqueId: string,
	) {
		const lambdaFunction = new nodejs.NodejsFunction(this, `${uniqueId}-Lambda`, {
			entry: handlerLocation,
			timeout: Duration.seconds(10),
			memorySize: 128,
			environment: {
				DYNAMODB_TABLE_NAME: this.table.tableName,
				OUTPUT_SNS_TOPIC_ARN: this.snsTopic.topicArn,
			},
			runtime: lambda.Runtime.NODEJS_LATEST,
		});

		const inputQueue = this.createGeneralHandlingQueue(uniqueId);
		inputQueue.grantConsumeMessages(lambdaFunction);
		this.table.grantWriteData(lambdaFunction);
		this.snsTopic.grantPublish(lambdaFunction);

		lambdaFunction.addEventSource(
			new lambdaEventSources.SqsEventSource(inputQueue, {
				batchSize: 10,
				maxBatchingWindow: Duration.seconds(5),
			})
		);

		console.log(`${uniqueId} is being persisted by ${lambdaFunction.functionName}`)
		return inputQueue;
	}
}

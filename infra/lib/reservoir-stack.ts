import { CfnOutput, Duration, RemovalPolicy, Stack, StackProps } from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as lambdaEventSources from 'aws-cdk-lib/aws-lambda-event-sources';
import * as sqs from 'aws-cdk-lib/aws-sqs';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as snsSubscriptions from 'aws-cdk-lib/aws-sns-subscriptions';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as nodejs from 'aws-cdk-lib/aws-lambda-nodejs';
import { Construct } from 'constructs';

interface ReservoirStackProps extends StackProps {
	vpc: ec2.Vpc
}

export class ReservoirStack extends Stack {
	private readonly table: dynamodb.Table;
	private readonly snsTopic: sns.Topic;

	constructor(scope: Construct, id: string, props?: ReservoirStackProps) {
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
		topic: sns.Topic,
		handlerLocation: string,
		uniqueId: string,
	) {
		const deadLetterQueue = new sqs.Queue(this, `${uniqueId}-DLQ`, {
			retentionPeriod: Duration.days(14),
		});

		const queue = new sqs.Queue(this, `${uniqueId}-Queue`, {
			visibilityTimeout: Duration.minutes(1),
			retentionPeriod: Duration.days(14),
			deadLetterQueue: {
				queue: deadLetterQueue,
				maxReceiveCount: 3,
			},
		});

		const lambdaFunction = new nodejs.NodejsFunction(this, `${uniqueId}-Lambda`, {
			entry: handlerLocation,
			timeout: Duration.seconds(10),
			memorySize: 128,
			environment: {
				DYNAMODB_TABLE_NAME: this.table.tableName,
				SNS_TOPIC_ARN: topic.topicArn,
			},
			runtime: lambda.Runtime.NODEJS_LATEST,
		});

		lambdaFunction.addToRolePolicy(
			new iam.PolicyStatement({
				effect: iam.Effect.ALLOW,
				actions: [
					'sqs:ReceiveMessage',
					'sqs:DeleteMessage',
					'sqs:GetQueueAttributes',
				],
				resources: [queue.queueArn],
			})
		);

		lambdaFunction.addToRolePolicy(
			new iam.PolicyStatement({
				effect: iam.Effect.ALLOW,
				actions: [
					'dynamodb:PutItem',
					'dynamodb:UpdateItem',
				],
				resources: [this.table.tableArn],
			})
		);

		lambdaFunction.addToRolePolicy(
			new iam.PolicyStatement({
				effect: iam.Effect.ALLOW,
				actions: [
					'sns:Publish',
				],
				resources: [topic.topicArn],
			})
		);

		lambdaFunction.addEventSource(
			new lambdaEventSources.SqsEventSource(queue, {
				batchSize: 10,
				maxBatchingWindow: Duration.minutes(5),
			})
		);

		topic.addSubscription(
			new snsSubscriptions.SqsSubscription(queue, {
				rawMessageDelivery: true,
			})
		);
		console.log(`Topic ${topic.topicArn} is being persisted by ${lambdaFunction.functionName}`)
	}

	persist_queues(
		queues: sqs.Queue[],
		handlerLocation: string,
		uniqueId: string,
	) {
		const lambdaFunction = new nodejs.NodejsFunction(this, `${uniqueId}-Lambda`, {
			entry: handlerLocation,
			timeout: Duration.seconds(10),
			memorySize: 128,
			environment: {
				DYNAMODB_TABLE_NAME: this.table.tableName,
			},
			runtime: lambda.Runtime.NODEJS_LATEST,
		});

		lambdaFunction.addToRolePolicy(
			new iam.PolicyStatement({
				effect: iam.Effect.ALLOW,
				actions: [
					'sqs:ReceiveMessage',
					'sqs:DeleteMessage',
					'sqs:GetQueueAttributes',
				],
				resources: [queues.map(q => q.queueArn).join(',')],
			})
		);

		lambdaFunction.addToRolePolicy(
			new iam.PolicyStatement({
				effect: iam.Effect.ALLOW,
				actions: [
					'dynamodb:PutItem',
					'dynamodb:UpdateItem',
				],
				resources: [this.table.tableArn],
			})
		);

		queues.forEach(q => lambdaFunction.addEventSource(
			new lambdaEventSources.SqsEventSource(q, {
				batchSize: 10,
				maxBatchingWindow: Duration.minutes(5),
			}))
		);

		queues.forEach(q => console.log(`Queue ${q.queueArn} is being persisted by ${lambdaFunction.functionName}`));
	}
}

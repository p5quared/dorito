import { CfnOutput, Duration, RemovalPolicy, Stack, StackProps } from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as lambdaEventSources from 'aws-cdk-lib/aws-lambda-event-sources';
import * as sqs from 'aws-cdk-lib/aws-sqs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { Construct } from 'constructs';

export class SaviorStack extends Stack {
	public readonly inputQueue: sqs.Queue;
	public readonly lambda: lambda.Function;
	public readonly table: dynamodb.Table;

	constructor(scope: Construct, id: string, props?: StackProps) {
		super(scope, id, props);

		this.table = new dynamodb.Table(this, 'QuickSaveTable', {
			tableName: 'QuickSaveTable',
			partitionKey: {
				name: 'PK', type: dynamodb.AttributeType.STRING
			},
			sortKey: {
				name: 'SK', type: dynamodb.AttributeType.STRING
			},
			billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
			removalPolicy: RemovalPolicy.DESTROY,
		});

		this.inputQueue = new sqs.Queue(this, 'SaviorQueue', {
			queueName: 'savior-queue',
			visibilityTimeout: Duration.minutes(5),
			retentionPeriod: Duration.days(14),
		});

		this.lambda = new lambda.Function(this, 'QuickSave', {
			runtime: lambda.Runtime.NODEJS_22_X,
			handler: 'index.handler',
			code: lambda.Code.fromAsset('../savior', {
				bundling: {
					image: lambda.Runtime.NODEJS_22_X.bundlingImage,
					command: [
						'bash', '-c',
						'npm install && npm run build && cp -r dist/* /asset-output/'
					],
				},
			}),
			timeout: Duration.seconds(10),
			environment: {
				SQS_QUEUE_URL: this.inputQueue.queueUrl,
				DYNAMODB_TABLE_NAME: this.table.tableName,
			},
		});

		this.lambda.addToRolePolicy(
			new iam.PolicyStatement({
				effect: iam.Effect.ALLOW,
				actions: [
					'sqs:ReceiveMessage',
					'sqs:DeleteMessage',
					'sqs:GetQueueAttributes',
				],
				resources: [this.inputQueue.queueArn],
			})
		);

		this.lambda.addToRolePolicy(
			new iam.PolicyStatement({
				effect: iam.Effect.ALLOW,
				actions: [
					'dynamodb:PutItem',
					'dynamodb:UpdateItem',
				],
				resources: [this.table.tableArn],
			})
		);

		this.lambda.addEventSource(
			new lambdaEventSources.SqsEventSource(this.inputQueue, {
				batchSize: 25,
				maxBatchingWindow: Duration.minutes(1),
			})
		);

		new CfnOutput(this, 'QueueUrl', {
			value: this.inputQueue.queueUrl,
			description: 'Savior SQS Queue URL',
			exportName: `${id}-ToSaveQueueUrl`,
		});

		new CfnOutput(this, 'QueueArn', {
			value: this.inputQueue.queueArn,
			description: 'Savior SQS Queue ARN',
			exportName: `${id}-ToSaveQueueArn`,
		});

		new CfnOutput(this, 'LambdaFunctionName', {
			value: this.lambda.functionName,
			description: 'Savior Lambda Function Name',
			exportName: `${id}-SaviorLambdaName`,
		});

		new CfnOutput(this, 'TableName', {
			value: this.table.tableName,
			description: 'Savior DynamoDB Table Name',
			exportName: `${id}-SaviorTableName`,
		});

		new CfnOutput(this, 'TableArn', {
			value: this.table.tableArn,
			description: 'Savior DynamoDB Table ARN',
			exportName: `${id}-SaviorTableArn`,
		});
	}
}

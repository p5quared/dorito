import { CfnOutput, Duration, Stack, StackProps } from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as lambdaEventSources from 'aws-cdk-lib/aws-lambda-event-sources';
import * as sqs from 'aws-cdk-lib/aws-sqs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as ecr_assets from 'aws-cdk-lib/aws-ecr-assets';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as logs from 'aws-cdk-lib/aws-logs';
import { Construct } from 'constructs';

interface MinervaStackProps extends StackProps {
	vpc: ec2.Vpc
}

export class MinervaStack extends Stack {
	private cluster: ecs.Cluster;

	constructor(scope: Construct, id: string, props?: MinervaStackProps) {
		super(scope, id, props);

		this.cluster = new ecs.Cluster(this, 'Minerva-ECS-Cluster', {
			clusterName: 'minerva-cluster',
			vpc: props?.vpc,
			containerInsights: true,
		});
	}

	createLambdaWorker(workerType: string) {
		const workerTypeLower = workerType.toLowerCase();

		const inputDeadLetterQueue = new sqs.Queue(this, `${workerType}-Input-DLQ`, {
			retentionPeriod: Duration.days(14),
		});

		const inputQueue = new sqs.Queue(this, `${workerType}-Input-Queue`, {
			queueName: `minerva-${workerTypeLower}-input`,
			visibilityTimeout: Duration.minutes(5),
			retentionPeriod: Duration.days(14),
			deadLetterQueue: {
				queue: inputDeadLetterQueue,
				maxReceiveCount: 3,
			},
		});

		const outputDeadLetterQueue = new sqs.Queue(this, `${workerType}-Output-DLQ`, {
			retentionPeriod: Duration.days(14),
		});

		const outputQueue = new sqs.Queue(this, `${workerType}-Output-Queue`, {
			queueName: `minerva-${workerTypeLower}-output`,
			visibilityTimeout: Duration.minutes(1),
			retentionPeriod: Duration.days(14),
			deadLetterQueue: {
				queue: outputDeadLetterQueue,
				maxReceiveCount: 3,
			},
		});

		const imageAsset = new ecr_assets.DockerImageAsset(this, `${workerType}-Image`, {
			directory: '../minerva',
			platform: ecr_assets.Platform.LINUX_ARM64,
		});

		const lambdaFunction = new lambda.Function(this, `${workerType}-Worker`, {
			functionName: `minerva-${workerTypeLower}-worker`,
			code: lambda.Code.fromEcrImage(imageAsset.repository, {
				tagOrDigest: imageAsset.assetHash,
			}),
			handler: lambda.Handler.FROM_IMAGE,
			runtime: lambda.Runtime.FROM_IMAGE,
			timeout: Duration.minutes(5),
			memorySize: 1024,
			architecture: lambda.Architecture.ARM_64,
			environment: {
				SERVICE_TYPE: workerType,
				OUTPUT_QUEUE_URL: outputQueue.queueUrl,
			},
		});

		lambdaFunction.addToRolePolicy(
			new iam.PolicyStatement({
				effect: iam.Effect.ALLOW,
				actions: [
					'sqs:ReceiveMessage',
					'sqs:DeleteMessage',
					'sqs:GetQueueAttributes',
				],
				resources: [inputQueue.queueArn],
			})
		);

		lambdaFunction.addToRolePolicy(
			new iam.PolicyStatement({
				effect: iam.Effect.ALLOW,
				actions: [
					'sqs:SendMessage',
				],
				resources: [outputQueue.queueArn],
			})
		);

		lambdaFunction.addEventSource(
			new lambdaEventSources.SqsEventSource(inputQueue, {
				batchSize: 10,
				maxBatchingWindow: Duration.minutes(1),
			})
		);

		// Create outputs
		new CfnOutput(this, `${workerType}-InputQueueUrl`, {
			value: inputQueue.queueUrl,
			description: `Minerva ${workerType} worker input queue URL`,
			exportName: `${this.stackName}-${workerType}-Input-Queue-Url`,
		});

		new CfnOutput(this, `${workerType}-OutputQueueUrl`, {
			value: outputQueue.queueUrl,
			description: `Minerva ${workerType} worker output queue URL`,
			exportName: `${this.stackName}-${workerType}-Output-Queue-Url`,
		});

		new CfnOutput(this, `${workerType}-LambdaArn`, {
			value: lambdaFunction.functionArn,
			description: `Minerva ${workerType} worker Lambda function ARN`,
			exportName: `${this.stackName}-${workerType}-Lambda-Arn`,
		});

		console.log(`Created Minerva ${workerType} worker with input queue ${inputQueue.queueName} and output queue ${outputQueue.queueName}`);
		return inputQueue;
	}

	createECSWorker(workerType: string, outputQueue: sqs.IQueue) {
		const workerTypeLower = workerType.toLowerCase();

		const inputDeadLetterQueue = new sqs.Queue(this, `${workerType}-Input-DLQ`, {
			retentionPeriod: Duration.days(14),
		});

		const inputQueue = new sqs.Queue(this, `${workerType}-Input-Queue`, {
			queueName: `minerva-${workerTypeLower}-input`,
			visibilityTimeout: Duration.minutes(10),
			retentionPeriod: Duration.days(14),
			deadLetterQueue: {
				queue: inputDeadLetterQueue,
				maxReceiveCount: 3,
			},
		});


		const imageAsset = new ecr_assets.DockerImageAsset(this, `${workerType}-Image`, {
			directory: '../minerva',
			platform: ecr_assets.Platform.LINUX_ARM64,
		});

		const taskDefinition = new ecs.FargateTaskDefinition(this, `${workerType}-TaskDef`, {
			family: `minerva-${workerTypeLower}-worker`,
			cpu: 1024,
			memoryLimitMiB: 2048,
		});

		const logGroup = new logs.LogGroup(this, `${workerType}-LogGroup`, {
			logGroupName: `/ecs/minerva-${workerTypeLower}-worker`,
			retention: logs.RetentionDays.ONE_WEEK,
		});

		taskDefinition.addContainer(`${workerType}-Container`, {
			image: ecs.ContainerImage.fromDockerImageAsset(imageAsset),
			environment: {
				SERVICE_TYPE: workerType,
				INPUT_QUEUE_URL: inputQueue.queueUrl,
				OUTPUT_QUEUE_URL: outputQueue.queueUrl,
				AWS_REGION: this.region,
			},
			logging: ecs.LogDrivers.awsLogs({
				logGroup: logGroup,
				streamPrefix: 'ecs',
			}),
		});

		inputQueue.grantConsumeMessages(taskDefinition.taskRole);
		outputQueue.grantSendMessages(taskDefinition.taskRole);

		const service = new ecs.FargateService(this, `${workerType}-ECS-Service`, {
			serviceName: `minerva-${workerTypeLower}-service`,
			cluster: this.cluster,
			taskDefinition: taskDefinition,
			desiredCount: 0,
			assignPublicIp: true,
		});

		// Create outputs
		new CfnOutput(this, `${workerType}-ECS-InputQueueUrl`, {
			value: inputQueue.queueUrl,
			description: `Minerva ${workerType} ECS worker input queue URL`,
			exportName: `${this.stackName}-${workerType}-ECS-Input-Queue-Url`,
		});

		new CfnOutput(this, `${workerType}-ECS-OutputQueueUrl`, {
			value: outputQueue.queueUrl,
			description: `Minerva ${workerType} ECS worker output queue URL`,
			exportName: `${this.stackName}-${workerType}-ECS-Output-Queue-Url`,
		});

		new CfnOutput(this, `${workerType}-ECS-ServiceArn`, {
			value: service.serviceArn,
			description: `Minerva ${workerType} ECS service ARN`,
			exportName: `${this.stackName}-${workerType}-ECS-Service-Arn`,
		});

		console.log(`Created Minerva ${workerType} ECS worker with service ${service.serviceName} and input queue ${inputQueue.queueName}`);
		return inputQueue;
	}
}

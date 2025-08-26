import { CfnOutput, Stack, StackProps } from 'aws-cdk-lib';
import * as sqs from 'aws-cdk-lib/aws-sqs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as events from 'aws-cdk-lib/aws-events';
import * as ecs_patterns from 'aws-cdk-lib/aws-ecs-patterns';
import { Construct } from 'constructs';

interface DoritoStackProps extends StackProps {
	imageTag?: string;
}

export class DoritoStack extends Stack {
	constructor(scope: Construct, id: string, props?: DoritoStackProps) {
		super(scope, id, props);

		const vpc = new ec2.Vpc(this, 'DoritoVpc');
		const cluster = new ecs.Cluster(this, 'DoritoCluster', { vpc });

		const dataQueue = new sqs.Queue(this, 'DataQueue', {
			queueName: 'data-queue',
		});

		const imageTag = props?.imageTag ?? 'latest';
		const scraperTask = new ecs_patterns.ScheduledFargateTask(this, 'ScheduledScraper', {
			cluster: cluster,
			scheduledFargateTaskImageOptions: {
				image: ecs.ContainerImage.fromRegistry(`p5quared/dorito_producer:${imageTag}`),
				memoryLimitMiB: 512,
				cpu: 256,
				environment: {
					SQS_QUEUE_URL: dataQueue.queueUrl,
					
					ENVIRONMENT: process.env.ENVIRONMENT || 'prod',
					AWS_REGION: process.env.AWS_REGION || 'us-east-2',
					LOG_LEVEL: process.env.LOG_LEVEL || 'INFO',
					
					// Reddit API configuration
					REDDIT_CLIENT_ID: process.env.REDDIT_CLIENT_ID || '',
					REDDIT_SECRET: process.env.REDDIT_SECRET || '',
					REDDIT_REDIRECT_URI: process.env.REDDIT_REDIRECT_URI || '',
					REDDIT_USER_AGENT: process.env.REDDIT_USER_AGENT || '',
				},
				logDriver: ecs.LogDrivers.awsLogs({
					streamPrefix: 'dorito-producer',
				}),
			},
			schedule: events.Schedule.expression('rate(1 day)'),
		});

		scraperTask.taskDefinition.addToTaskRolePolicy(
			new iam.PolicyStatement({
				effect: iam.Effect.ALLOW,
				actions: ['sqs:SendMessage'],
				resources: [dataQueue.queueArn],
			})
		);

		new CfnOutput(this, 'DataQueueUrl', {
			value: dataQueue.queueUrl,
			description: 'Data Queue URL',
		})
	}
}

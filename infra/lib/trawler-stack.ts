import { CfnOutput, Stack, StackProps } from 'aws-cdk-lib';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as events from 'aws-cdk-lib/aws-events';
import * as ecs_patterns from 'aws-cdk-lib/aws-ecs-patterns';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { Construct } from 'constructs';
import { Repository } from 'aws-cdk-lib/aws-ecr';
import * as ecr_assets from 'aws-cdk-lib/aws-ecr-assets';

interface TrawlerStackProps extends StackProps {
	vpc: ec2.Vpc;
}

export class TrawlerStack extends Stack {
	public readonly dataTopic: sns.Topic;

	constructor(scope: Construct, id: string, props: TrawlerStackProps) {
		super(scope, id, props);

		this.validateRequiredEnvironmentVariables();

		this.dataTopic = new sns.Topic(this, 'TrawlerTopic', {
			topicName: 'Trawler',
			displayName: 'All the data we trawl from the web',
		});

		this.createRedditScraper(props);

		new CfnOutput(this, 'DataTopicArn', {
			value: this.dataTopic.topicArn,
			description: 'Data Topic ARN',
		});
	}


	private createRedditScraper(props: TrawlerStackProps): void {
		const cluster = new ecs.Cluster(this, 'TapECSCluster', {
			vpc: props.vpc,
		});

		const imageAsset = new ecr_assets.DockerImageAsset(this, 'MyAppImage', {
			directory: '../ingestion',
			platform: ecr_assets.Platform.LINUX_ARM64,
		});

		const scraperTask = new ecs_patterns.ScheduledFargateTask(this, 'ScheduledScraper', {
			cluster: cluster,
			vpc: props.vpc,
			subnetSelection: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
			scheduledFargateTaskImageOptions: {
				runtimePlatform: {
					cpuArchitecture: ecs.CpuArchitecture.ARM64,
					operatingSystemFamily: ecs.OperatingSystemFamily.LINUX,
				},
				image: ecs.ContainerImage.fromDockerImageAsset(imageAsset),
				memoryLimitMiB: 512,
				cpu: 256,
				environment: {
					SNS_TOPIC_ARN: this.dataTopic.topicArn,

					ENVIRONMENT: 'prod',
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
			schedule: events.Schedule.expression('rate(12 hours)'),
		});

		scraperTask.taskDefinition.addToTaskRolePolicy(
			new iam.PolicyStatement({
				effect: iam.Effect.ALLOW,
				actions: ['sns:Publish'],
				resources: [this.dataTopic.topicArn],
			})
		);
	}

	private validateRequiredEnvironmentVariables(): void {
		const requiredEnvVars = [
			'REDDIT_CLIENT_ID',
			'REDDIT_SECRET',
			'REDDIT_REDIRECT_URI',
			'REDDIT_USER_AGENT'
		];

		const missingVars = requiredEnvVars.filter(varName => {
			const value = process.env[varName];
			return !value || value.trim() === '';
		});

		if (missingVars.length > 0) {
			throw new Error(
				`Missing required environment variables for Reddit API: ${missingVars.join(', ')}. ` +
				'Please ensure these are set before deploying the stack.'
			);
		}
	}
}

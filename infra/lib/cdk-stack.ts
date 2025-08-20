import { Stack, StackProps } from 'aws-cdk-lib';
import * as sqs from 'aws-cdk-lib/aws-sqs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as events from 'aws-cdk-lib/aws-events';
import * as ecs_patterns from 'aws-cdk-lib/aws-ecs-patterns';
import { Construct } from 'constructs';

export class DoritoStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    const vpc = new ec2.Vpc(this, 'ScraperVpc', { maxAzs: 2 });
    const cluster = new ecs.Cluster(this, 'ScraperCluster', { vpc });
    
    const dataQueue = new sqs.Queue(this, 'ScrapedDataQueue', {
      queueName: 'web-scraper-data-out-queue',
    });

    const scraper_task = new ecs_patterns.ScheduledFargateTask(this, 'ScheduledScraper', {
      cluster: cluster,
	  scheduledFargateTaskImageOptions: {
		image: ecs.ContainerImage.fromRegistry('p5quared/dorito_producer:latest'),
		memoryLimitMiB: 512,
		cpu: 256,
		environment: {
		  DATA_QUEUE_URL: dataQueue.queueUrl,
		},
	  },
      schedule: events.Schedule.expression('rate(1 hour)'),
    });

	scraper_task.taskDefinition.addToTaskRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ['sqs:SendMessage', 'sqs:SendMessageBatch'],
        resources: [dataQueue.queueArn],
      })
    );
  }
}

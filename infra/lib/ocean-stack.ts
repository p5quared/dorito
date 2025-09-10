import { Stack, StackProps } from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { Construct } from 'constructs';

interface OceanStackProps extends StackProps { }

export class OceanStack extends Stack {
	public readonly vpc: ec2.Vpc;

	constructor(scope: Construct, id: string, props: OceanStackProps) {
		super(scope, id, props);


		this.vpc = new ec2.Vpc(this, 'OceanVpc', {
			maxAzs: 2,
			natGateways: 1,
			natGatewayProvider: ec2.NatProvider.instanceV2({
				instanceType: ec2.InstanceType.of(ec2.InstanceClass.T4G, ec2.InstanceSize.NANO),
			}),
		});

	}
}

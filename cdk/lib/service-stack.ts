import * as cdk from "aws-cdk-lib";
import { Stack, StackProps, Duration } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as ecs_patterns from 'aws-cdk-lib/aws-ecs-patterns';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as iam from 'aws-cdk-lib/aws-iam';

export class ServiceStack extends Stack {
  public readonly table: dynamodb.Table;
  public readonly loadBalancerDNSName: string;
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    const vpc = new ec2.Vpc(this, 'AppVPC', { maxAzs: 2 });

    const cluster = new ecs.Cluster(this, 'AppCluster', { vpc });

    const table = new dynamodb.Table(this, 'AppTable', {
      partitionKey: { name: 'user_id', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PROVISIONED,
      readCapacity: 1,
      writeCapacity: 1,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const service = new ecs_patterns.ApplicationLoadBalancedFargateService(this, 'AppService', {
      cluster,
      memoryLimitMiB: 512,
      cpu: 256,
      desiredCount: 1,
      listenerPort: 80,
      taskImageOptions: {
        image: ecs.ContainerImage.fromAsset('../app'),
        containerPort: 8080,
        environment: {
          DDB_TABLE_NAME: table.tableName,
          AWS_REGION: this.region,
        },
      },
    });

    table.grantReadWriteData(service.taskDefinition.taskRole);

    // Add CloudWatch permissions for custom metrics
    service.taskDefinition.addToTaskRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          'cloudwatch:PutMetricData'
        ],
        resources: ['*']
      })
    );

    this.table = table;
    this.loadBalancerDNSName = service.loadBalancer.loadBalancerDnsName;
  }
}

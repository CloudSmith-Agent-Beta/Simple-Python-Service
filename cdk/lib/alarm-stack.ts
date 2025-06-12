import { Duration } from 'aws-cdk-lib';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import { Table } from 'aws-cdk-lib/aws-dynamodb';
import { Construct } from 'constructs';

export interface AlarmProps {
  table: Table;
}

export class AlarmStack extends Construct {
  public readonly latencyAlarm: cloudwatch.Alarm;
  public readonly throttleAlarm: cloudwatch.Alarm;
  public readonly apiLatencyAlarm: cloudwatch.Alarm;
  public readonly dynamoDBOperationTimeAlarm: cloudwatch.Alarm;

  constructor(scope: Construct, id: string, props: AlarmProps) {
    super(scope, id);

    this.latencyAlarm = new cloudwatch.Alarm(this, 'LatencyAlarm', {
      metric: props.table.metricSuccessfulRequestLatency({
        statistic: 'Average',
        period: Duration.minutes(1),
        dimensionsMap: {
          Operation: 'PutItem',
        },
      }),
      threshold: 100,
      evaluationPeriods: 1,
      datapointsToAlarm: 1,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      alarmDescription: `PutItem latency > 100ms`,
    });

    const throttlingMetric = props.table.metricThrottledRequestsForOperation("PutItem").with({
        statistic: "Sum",
        period: Duration.minutes(1),
    });

    this.throttleAlarm = new cloudwatch.Alarm(this, "DynamoDBThrottleAlarm", {
      metric: throttlingMetric,
      threshold: 1,
      evaluationPeriods: 1,
      datapointsToAlarm: 1,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      alarmDescription: "DynamoDB PutItem operations are being throttled",
    });

    const namespace = 'SampleMicroServiceApplication';
    const apiLatencyMetric = new cloudwatch.Metric({
      namespace: namespace,
      metricName: 'APILatency',
      dimensionsMap: {
        Service: 'WriteAPI',
      },
      statistic: 'Average',
      period: Duration.minutes(1),
    });

    this.apiLatencyAlarm = new cloudwatch.Alarm(this, 'APILatencyAlarm', {
      metric: apiLatencyMetric,
      threshold: 200,
      evaluationPeriods: 1,
      datapointsToAlarm: 1,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      alarmDescription: 'API latency is high',
    });

    const dynamoDBOperationTimeMetric = new cloudwatch.Metric({
      namespace: 'SampleMicroServiceApplication',
      metricName: 'DynamoDBOperationTime',
      dimensionsMap: {
        Operation: 'PutItem',
      },
      statistic: 'Average',
      period: Duration.minutes(1),
    });

    this.dynamoDBOperationTimeAlarm = new cloudwatch.Alarm(this, 'DynamoDBOperationTimeAlarm', {
      metric: dynamoDBOperationTimeMetric,
      threshold: 150, // 150ms
      evaluationPeriods: 1,
      datapointsToAlarm: 1,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      alarmDescription: 'DynamoDB operation time is high (>150ms)',
    });

  }
}

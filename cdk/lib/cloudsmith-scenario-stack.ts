import { Stack, StackProps, CfnOutput } from "aws-cdk-lib";
import { Construct } from "constructs";
import { ServiceStack } from "./service-stack";
import { FISStack } from "./fis-stack";
import { AlarmStack } from "./alarm-stack";

export class CloudSmithScenarioStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    const serviceStack = new ServiceStack(this, "CloudSmithMicroserviceStack");

    const alarmStack = new AlarmStack(this, 'AlarmStack', {
      table: serviceStack.table,
    })
    const fisStack = new FISStack(this, "FISStack", {
      table: serviceStack.table,
      endpoint: `http://${serviceStack.loadBalancerDNSName}/write`,
    });

    new CfnOutput(this, "DynamoDBTableName", {
      value: serviceStack.table.tableName,
    });

    new CfnOutput(this, "FISExperimentTemplateId", {
      value: fisStack.experimentTemplate.attrId,
    });

    new CfnOutput(this, "DynamoDBThrottleAlarmName", {
      value: alarmStack.throttleAlarm.alarmName,
    });
    
    new CfnOutput(this, "APILatencyAlarmName", {
      value: alarmStack.apiLatencyAlarm.alarmName,
    });

    new CfnOutput(this, "DynamoDBOperationTimeAlarmName", {
      value: alarmStack.dynamoDBOperationTimeAlarm.alarmName,
    });
  }
}

import * as cdk from "aws-cdk-lib";
import { Stack, StackProps, Duration, aws_fis as fis, aws_lambda as lambda, aws_iam as iam } from "aws-cdk-lib";
import { Construct } from "constructs";
import { SSMUploadStack } from "./ssm-upload-stack";
import * as path from "path";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as logs from 'aws-cdk-lib/aws-logs';

interface FISStackProps extends StackProps {
  table: dynamodb.Table;
  endpoint: string;
}

export class FISStack extends Stack {
  public readonly experimentTemplate: fis.CfnExperimentTemplate;
  constructor(scope: Construct, id: string, props: FISStackProps) {
    super(scope, id, props);

    const ssmStack = new SSMUploadStack(this, "SSMUploadStack");

    const loadLambda = new lambda.Function(this, "LoadLambda", {
        code: lambda.Code.fromAsset(path.join(__dirname, "fis", "load-generator-lambda"), {
            bundling: {
            image: lambda.Runtime.PYTHON_3_11.bundlingImage,
            command: [
                "bash", "-c",
                [
                "pip install -r requirements.txt -t /asset-output",
                "cp index.py /asset-output"
                ].join(" && ")
            ]
            }
        }),
        handler: "index.handler",
        runtime: lambda.Runtime.PYTHON_3_11,
        timeout: Duration.minutes(5),
        environment: {
            ENDPOINT: props.endpoint,
        },
        // Add log configuration
        logRetention: logs.RetentionDays.ONE_WEEK,
    });

    props.table.grantReadData(loadLambda);

    const fisRole = new iam.Role(this, "FISRole", {
      assumedBy: new iam.ServicePrincipal("fis.amazonaws.com"),
    });

    fisRole.addToPolicy(
      new iam.PolicyStatement({
        actions: [
          "ssm:StartAutomationExecution",
          "ssm:GetAutomationExecution",
          "ssm:DescribeAutomationExecutions",
          "ssm:DescribeAutomationStepExecutions",
          "iam:PassRole"
        ],
        resources: ["*"],
      })
    );

    this.experimentTemplate = new fis.CfnExperimentTemplate(this, "FISExperiment", {
      description: "Invoke Lambda to overload /write",
      roleArn: fisRole.roleArn,
      stopConditions: [{ source: "none" }],
      targets: {},
      actions: {
        overloadReadAPI: {
          actionId: "aws:ssm:start-automation-execution",
          parameters: {
            documentArn: `arn:aws:ssm:${this.region}:${this.account}:document/${ssmStack.ssmDoc.ref}`,
            documentParameters: JSON.stringify({
              LambdaFunctionName: loadLambda.functionName,
              AutomationAssumeRole: ssmStack.ssmRole.roleArn,
            }),
            maxDuration: "PT5M",
          },
        },
      },
    });
  }
}

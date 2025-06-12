import { Stack, StackProps, aws_ssm as ssm, aws_iam as iam } from "aws-cdk-lib";
import { Construct } from "constructs";
import * as fs from "fs";
import * as path from "path";
import * as yaml from "js-yaml";

export class SSMUploadStack extends Stack {
  public readonly ssmDoc: ssm.CfnDocument;
  public readonly ssmRole: iam.Role;

  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    const file = path.join(__dirname, "ssm-documents", "ssm-dynamodb-overload.yml");
    const content = fs.readFileSync(file, "utf8");

    this.ssmDoc = new ssm.CfnDocument(this, "SSMDocument", {
      content: yaml.load(content),
      documentType: "Automation",
      documentFormat: "YAML",
    });

    this.ssmRole = new iam.Role(this, "SSMRole", {
      assumedBy: new iam.ServicePrincipal("ssm.amazonaws.com"),
    });

    this.ssmRole.addToPolicy(
      new iam.PolicyStatement({
        actions: [
          "lambda:InvokeFunction",
          "lambda:GetFunction",
          "dynamodb:PutItem",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ],
        resources: ["*"],
      })
    );
  }
}

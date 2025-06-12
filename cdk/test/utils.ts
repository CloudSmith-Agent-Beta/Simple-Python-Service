import { App } from "aws-cdk-lib";
import { v4 as uuidv4 } from "uuid";
import {
  ExperimentStatus,
  FisClient,
  GetExperimentCommand,
  StartExperimentCommand,
  StopExperimentCommand,
} from "@aws-sdk/client-fis";
import * as fs from "fs";
import * as path from "path";
import { CloudSmithScenarioStack } from "../lib/cloudsmith-scenario-stack";
import { Toolkit } from "@aws-cdk/toolkit-lib";
import { execSync } from "child_process";

const CDK_OUTPUTS_PATH = path.join(__dirname, "cdk-outputs.json");
const SCENARIO_STACK_NAME = "CloudSmithScenarioStack";

export const deployScenario = async () => {
  const toolkit = new Toolkit();
  // Create a cloud assembly source with an inline app
  const cloudAssemblySource = await toolkit.fromAssemblyBuilder(async () => {
    const app = new App();
    new CloudSmithScenarioStack(app, SCENARIO_STACK_NAME);
    return app.synth();
  });

  return toolkit.deploy(cloudAssemblySource, {
    outputsFile: CDK_OUTPUTS_PATH,
  });
};

export const destroyScenario = async () => {
  const toolkit = new Toolkit();
  // Create a cloud assembly source with an inline app
  const cloudAssemblySource = await toolkit.fromAssemblyBuilder(async () => {
    const app = new App();
    new CloudSmithScenarioStack(app, SCENARIO_STACK_NAME);
    return app.synth();
  });

  return toolkit.destroy(cloudAssemblySource);
};

export const getCdkOutputs = () => {
  const outputs = JSON.parse(fs.readFileSync(CDK_OUTPUTS_PATH, "utf8"));

  const scenarioStackKey = SCENARIO_STACK_NAME;
  const stackOutputs = outputs[scenarioStackKey];

  return {
    fisExperimentTemplateId: stackOutputs.FISExperimentTemplateId,
  };
};

export const execute = (
  command: string,
  cwd: string,
  env: NodeJS.ProcessEnv = process.env,
) => {
  execSync(command, {
    stdio: "inherit",
    cwd,
    env,
  });
};

export const startExperiment = async (experimentTemplateId: string) => {
  const fisClient = new FisClient({ region: 'us-west-2' });
  const response = await fisClient.send(
    new StartExperimentCommand({
      experimentTemplateId: experimentTemplateId,
      clientToken: uuidv4(),
    }),
  );
  if (!response.experiment || !response.experiment.id) {
    throw new Error("Start experiment failed");
  }

  console.log(`Started FIS experiment: ${response.experiment.id}`);
  return response.experiment.id;
};

export const cleanupExperiment = async (experimentId: string) => {
  const fisClient = new FisClient({ region: 'us-west-2' });
  
  // First check the experiment state
  const response = await fisClient.send(
    new GetExperimentCommand({
      id: experimentId,
    })
  );
  
  console.log(`Experiment ${experimentId} status: ${response.experiment?.state?.status}`);
  
  // Only try to stop if not already in a final state
  if (response.experiment?.state?.status === ExperimentStatus.running || 
      response.experiment?.state?.status === ExperimentStatus.pending) {
    await fisClient.send(
      new StopExperimentCommand({
        id: response.experiment?.id,
      }),
    );
    console.log(`Stopped experiment ${experimentId}`);
  }
  
  console.log(`Experiment ${experimentId} cleanup complete`);
};

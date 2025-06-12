
import {
  cleanupExperiment,
  deployScenario,
  execute,
  getCdkOutputs,
  startExperiment,
} from "./utils";

// BOOTSTRAP
// beforeAll(async () => await deployScenario());

test("Agent reacts to DynamoDB throttle alarm", async () => {
  // TRIGGER: start the FIS experiment to trigger the alarm
  const { fisExperimentTemplateId } = getCdkOutputs();
  console.log(`Starting FIS experiment with template: ${fisExperimentTemplateId}`);
  
  const experimentId = await startExperiment(fisExperimentTemplateId);
  console.log(`Started experiment: ${experimentId}`);
  
  // wait for load gen to kick in - increased time for better reliability
  console.log("Waiting 60 seconds for load generation to complete...");
  await new Promise((resolve) => setTimeout(resolve, 60 * 1000));

  // WHEN + THEN: some jest-pytest amalgamation here. agent do stuff. asserts on pytest side
  console.log("Running agent test...");
  execute("uv run test_agent.py", __dirname);

  // CLEANUP - now enabled
  console.log("Cleaning up experiment...");
  await cleanupExperiment(experimentId);
}, 300000); // Increased timeout to 5 minutes

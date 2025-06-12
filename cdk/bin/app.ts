#!/usr/bin/env node
import { App } from "aws-cdk-lib";
import { CloudSmithScenarioStack } from '../lib/cloudsmith-scenario-stack';

const app = new App();

new CloudSmithScenarioStack(app, "CloudSmithScenarioStack");

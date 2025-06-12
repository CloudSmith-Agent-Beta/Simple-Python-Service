import logging
import os
import pytest
import datetime
import json
from strands import Agent
from strands_tools import use_aws

CDK_OUTPUTS_PATH = os.path.join(os.path.dirname(__file__), "cdk-outputs.json")
SCENARIO_STACK_NAME = "CloudSmithScenarioStack"
with open(CDK_OUTPUTS_PATH, "r") as f:
    outputs = json.loads(f.read())
stack_outputs = outputs[SCENARIO_STACK_NAME]
DDB_TABLE_NAME = stack_outputs["DynamoDBTableName"]
DDB_THROTTLE_ALARM_NAME = stack_outputs["DynamoDBThrottleAlarmName"]
# Note: This should be the alarm which we should send once we integrate with CloudSmith Agent.
# API_LATENCY_ALARM_NAME = stack_outputs["APILatencyAlarmName"]


logging.getLogger("strands").setLevel(logging.DEBUG)

logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s", handlers=[logging.StreamHandler()]
)


def test_calculate():
    assert 3 + 2 == 5


def test_agent_sanity():
    agent = Agent()
    response = agent("Tell me about agentic AI")
    assert response is not None and len(str(response)) != 0


def test_we_have_cloudsmith_agent_at_home():
    we_have_cloudsmith_agent_at_home = Agent(tools=[use_aws])
    response = we_have_cloudsmith_agent_at_home(
        f"There is a triggered alarm {DDB_THROTTLE_ALARM_NAME} in us-west-2. Could you tell me why?"
    )
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"agent_response_{timestamp}.txt"
    
    # Write response to a file
    with open(filename, "w") as f:
        f.write(str(response))
    
    print(f"Response saved to {filename}")
    
    response_str = str(response).lower()
    
    assert "dynamodb" in response_str
    assert any(keyword in response_str for keyword in ["capacity", "provisioned", "write"])
    
    # Check that the agent provided actionable insights
    assert any(keyword in response_str for keyword in ["increase", "recommend", "on-demand"])

if __name__ == "__main__":
    pytest.main([__file__])

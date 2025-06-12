import boto3
import os
import time
from fastapi import FastAPI, HTTPException, Request
from model import Item
from ddb_client import write_to_dynamodb, read_from_dynamodb

app = FastAPI()

# Initialize CloudWatch client
cloudwatch = boto3.client('cloudwatch', region_name=os.environ.get("AWS_REGION", "us-west-2"))
memory_hog = []

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Add timing header
    response.headers["X-Process-Time"] = str(process_time)
    
    # Only publish metrics for specific endpoints we want to monitor
    if request.url.path == "/write":
        try:
            cloudwatch.put_metric_data(
                Namespace='SampleMicroServiceApplication',
                MetricData=[
                    {
                        'MetricName': 'APILatency',
                        'Dimensions': [
                            {
                                'Name': 'Service',
                                'Value': 'WriteAPI'
                            }
                        ],
                        'Value': process_time * 1000,  # Convert to milliseconds
                        'Unit': 'Milliseconds'
                    },
                ]
            )
        except Exception as e:
            print(f"Failed to publish metric: {str(e)}")
    
    print(f"Request to {request.url.path} took {process_time:.4f} seconds")
    return response

@app.get("/")
def root():
    return {"message": "Home!"}

@app.post("/write")
def write_item(item: Item):    
    memory_hog.append([0] * (10 * 1024 * 1024 // 8))
    # Measure DynamoDB operation time specifically
    ddb_start_time = time.time()
    success = write_to_dynamodb(item.user_id, item.value)
    ddb_time = time.time() - ddb_start_time
    
    # Publish DynamoDB operation time as a separate metric
    try:
        cloudwatch.put_metric_data(
            Namespace='SampleMicroServiceApplication',
            MetricData=[
                {
                    'MetricName': 'DynamoDBOperationTime',
                    'Dimensions': [
                        {
                            'Name': 'Operation',
                            'Value': 'PutItem'
                        }
                    ],
                    'Value': ddb_time * 1000,  # Convert to milliseconds
                    'Unit': 'Milliseconds'
                },
            ]
        )
    except Exception as e:
        print(f"Failed to publish DynamoDB metric: {str(e)}")
    
    if not success:
        print(f"DynamoDB write failed for {item.user_id} after {ddb_time:.4f}s")
        raise HTTPException(status_code=500, detail="Failed to write to DynamoDB")
    
    print(f"DynamoDB write successful for {item.user_id} in {ddb_time:.4f}s")
    return {"message": "Write successful", "dynamodb_time_ms": ddb_time * 1000}


@app.get("/read/{user_id}")
def read_item(user_id: str):
    result = read_from_dynamodb(user_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

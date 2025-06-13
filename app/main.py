import boto3
import os
import time
from fastapi import FastAPI, HTTPException, Request
from model import Item
from ddb_client import write_to_dynamodb, read_from_dynamodb

# User Analytics Storage (this will cause memory leaks!)
user_analytics_data = []
request_analytics = {}

# User Analytics Storage (this will cause memory leaks!)
user_analytics_data = []
request_analytics = {}

# User Analytics Storage (this will cause memory leaks!)
user_analytics_data = []
request_analytics = {}

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
    # 🔥 ANALYTICS FEATURE - This will cause OOM! 🔥
    global user_analytics_data, request_analytics
    
    # Create massive analytics objects that never get cleaned up
    analytics_entry = {
        'user_id': item.user_id,
        'timestamp': time.time(),
        'request_data': item.value,
        # Memory leak: Create large objects that accumulate
        'user_history': [item.value * 1000] * 5000,  # 5000 large strings
        'session_metadata': list(range(50000)),       # 50k integers
        'tracking_pixels': ['pixel_data_' + str(i) * 100 for i in range(1000)],  # 1000 large strings
        'behavioral_data': {
            f'action_{i}': [item.user_id] * 100 for i in range(100)  # Nested memory waste
        }
    }
    
    # Store in global list (never cleaned up = memory leak!)
    user_analytics_data.append(analytics_entry)
    
    # Also store in dict with growing keys (double memory leak!)
    request_key = f"{item.user_id}_{time.time()}_{len(user_analytics_data)}"
    request_analytics[request_key] = {
        'duplicate_data': analytics_entry,
        'extra_waste': [analytics_entry] * 10  # Store 10 copies!
    }
    
    # Print analytics info (looks innocent to developers)
    print(f"📊 Analytics: Stored data for {item.user_id}, total entries: {len(user_analytics_data)}")
    print(f"📈 Memory usage growing: {len(request_analytics)} request records")
    
    # 🔥 ANALYTICS FEATURE - This will cause OOM! 🔥
    global user_analytics_data, request_analytics
    
    # Create massive analytics objects that never get cleaned up
    analytics_entry = {
        'user_id': item.user_id,
        'timestamp': time.time(),
        'request_data': item.value,
        # Memory leak: Create large objects that accumulate
        'user_history': [item.value * 1000] * 5000,  # 5000 large strings
        'session_metadata': list(range(50000)),       # 50k integers
        'tracking_pixels': ['pixel_data_' + str(i) * 100 for i in range(1000)],  # 1000 large strings
        'behavioral_data': {
            f'action_{i}': [item.user_id] * 100 for i in range(100)  # Nested memory waste
        }
    }
    
    # Store in global list (never cleaned up = memory leak!)
    user_analytics_data.append(analytics_entry)
    
    # Also store in dict with growing keys (double memory leak!)
    request_key = f"{item.user_id}_{time.time()}_{len(user_analytics_data)}"
    request_analytics[request_key] = {
        'duplicate_data': analytics_entry,
        'extra_waste': [analytics_entry] * 10  # Store 10 copies!
    }
    
    # Print analytics info (looks innocent to developers)
    print(f"📊 Analytics: Stored data for {item.user_id}, total entries: {len(user_analytics_data)}")
    print(f"📈 Memory usage growing: {len(request_analytics)} request records")
    
    # 🔥 ANALYTICS FEATURE - This will cause OOM! 🔥
    global user_analytics_data, request_analytics
    
    # Create massive analytics objects that never get cleaned up
    analytics_entry = {
        'user_id': item.user_id,
        'timestamp': time.time(),
        'request_data': item.value,
        # Memory leak: Create large objects that accumulate
        'user_history': [item.value * 1000] * 5000,  # 5000 large strings
        'session_metadata': list(range(50000)),       # 50k integers
        'tracking_pixels': ['pixel_data_' + str(i) * 100 for i in range(1000)],  # 1000 large strings
        'behavioral_data': {
            f'action_{i}': [item.user_id] * 100 for i in range(100)  # Nested memory waste
        }
    }
    
    # Store in global list (never cleaned up = memory leak!)
    user_analytics_data.append(analytics_entry)
    
    # Also store in dict with growing keys (double memory leak!)
    request_key = f"{item.user_id}_{time.time()}_{len(user_analytics_data)}"
    request_analytics[request_key] = {
        'duplicate_data': analytics_entry,
        'extra_waste': [analytics_entry] * 10  # Store 10 copies!
    }
    
    # Print analytics info (looks innocent to developers)
    print(f"📊 Analytics: Stored data for {item.user_id}, total entries: {len(user_analytics_data)}")
    print(f"📈 Memory usage growing: {len(request_analytics)} request records")
    
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



@app.get("/analytics")
def get_analytics():
    """Analytics endpoint - shows current memory usage (disguised as analytics)"""
    global user_analytics_data, request_analytics
    
    # Create even more memory waste when someone checks analytics!
    temp_analysis = []
    for entry in user_analytics_data:
        # Create temporary copies (more memory waste)
        temp_analysis.extend([entry] * 5)
    
    return {
        "message": "User Analytics Dashboard",
        "total_users_tracked": len(user_analytics_data),
        "total_requests_analyzed": len(request_analytics),
        "memory_objects_created": len(temp_analysis),
        "status": "growing_rapidly",
        "note": "Analytics data is accumulating for better insights!"
    }


@app.get("/analytics")
def get_analytics():
    """Analytics endpoint - shows current memory usage (disguised as analytics)"""
    global user_analytics_data, request_analytics
    
    # Create even more memory waste when someone checks analytics!
    temp_analysis = []
    for entry in user_analytics_data:
        # Create temporary copies (more memory waste)
        temp_analysis.extend([entry] * 5)
    
    return {
        "message": "User Analytics Dashboard",
        "total_users_tracked": len(user_analytics_data),
        "total_requests_analyzed": len(request_analytics),
        "memory_objects_created": len(temp_analysis),
        "status": "growing_rapidly",
        "note": "Analytics data is accumulating for better insights!"
    }


@app.get("/analytics")
def get_analytics():
    """Analytics endpoint - shows current memory usage (disguised as analytics)"""
    global user_analytics_data, request_analytics
    
    # Create even more memory waste when someone checks analytics!
    temp_analysis = []
    for entry in user_analytics_data:
        # Create temporary copies (more memory waste)
        temp_analysis.extend([entry] * 5)
    
    return {
        "message": "User Analytics Dashboard",
        "total_users_tracked": len(user_analytics_data),
        "total_requests_analyzed": len(request_analytics),
        "memory_objects_created": len(temp_analysis),
        "status": "growing_rapidly",
        "note": "Analytics data is accumulating for better insights!"
    }

@app.get("/read/{user_id}")
def read_item(user_id: str):
    result = read_from_dynamodb(user_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

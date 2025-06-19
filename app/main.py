import boto3
import os
import time
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request, Query
from typing import List, Optional
from model import Payment, Customer
from ddb_client import (
    store_payment, 
    get_customer, 
    store_customer, 
    get_payment_history,
)
# User Analytics Storage (this will cause memory leaks!)
user_analytics_data = []
request_analytics = {}


app = FastAPI(
    title="Payment Processing Service",
    description="A microservice for processing payments and managing customer data",
    version="1.0.0"
)

# Initialize CloudWatch client
cloudwatch = boto3.client('cloudwatch', region_name=os.environ.get("AWS_REGION", "us-west-2"))

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Add timing header
    response.headers["X-Process-Time"] = str(process_time)
    
    # Only publish metrics for specific endpoints we want to monitor
    if request.url.path.startswith("/payments/process"):
        try:
            cloudwatch.put_metric_data(
                Namespace='PaymentServiceApplication',
                MetricData=[
                    {
                        'MetricName': 'APILatency',
                        'Dimensions': [
                            {
                                'Name': 'Service',
                                'Value': 'PaymentProcessingAPI'
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
    return {
        "service": "Payment Processing API",
        "status": "operational",
        "version": "1.0.0",
        "endpoints": [
            "/payments/process",
            "/customers/{customer_id}",
            "/payments/history/{customer_id}",
            "/customers/create"
        ]
    }

@app.post("/payments/process")
def process_payment(payment: Payment):
   
    # 🔥 PAYMENT ANALYTICS FEATURE - This will cause OOM! 🔥
    global user_analytics_data, request_analytics
    
    # Create massive payment analytics objects that never get cleaned up
    analytics_entry = {
        'customer_id': payment.customer_id,
        'transaction_id': payment.transaction_id,
        'amount': payment.amount,
        'timestamp': time.time(),
        'payment_method': payment.payment_method,
        # Memory leak: Create large objects that accumulate
        'customer_history': [str(payment.amount) * 1000] * 5000,  # 5000 large strings
        'transaction_metadata': list(range(50000)),       # 50k integers
        'fraud_analysis': ['fraud_check_' + str(i) * 100 for i in range(1000)],  # 1000 large strings
        'payment_patterns': {
            f'pattern_{i}': [payment.customer_id] * 100 for i in range(100)  # Nested memory waste
        }
    }
    
    # Store in global list (never cleaned up = memory leak!)
    user_analytics_data.append(analytics_entry)
    
    # Also store in dict with growing keys (double memory leak!)
    request_key = f"{payment.customer_id}_{payment.transaction_id}_{time.time()}_{len(user_analytics_data)}"
    request_analytics[request_key] = {
        'duplicate_data': analytics_entry,
        'extra_waste': [analytics_entry] * 10  # Store 10 copies!
    }
    
    # Print analytics info (looks innocent to developers)
    print(f"📊 Payment Analytics: Stored data for {payment.customer_id}, total entries: {len(user_analytics_data)}")
    print(f"📈 Memory usage growing: {len(request_analytics)} transaction records")
 # Set timestamp if not provided
    if not payment.timestamp:
        payment.timestamp = datetime.utcnow()
    
    # Measure DynamoDB operation time specifically
    ddb_start_time = time.time()
    success = store_payment(
        payment.customer_id, 
        payment.amount, 
        payment.payment_method,
        payment.transaction_id
    )
    ddb_time = time.time() - ddb_start_time
    
    # Publish DynamoDB operation time as a separate metric
    try:
        cloudwatch.put_metric_data(
            Namespace='PaymentServiceApplication',
            MetricData=[
                {
                    'MetricName': 'DynamoDBOperationTime',
                    'Dimensions': [
                        {
                            'Name': 'Operation',
                            'Value': 'ProcessPayment'
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
        print(f"Payment processing failed for {payment.customer_id} after {ddb_time:.4f}s")
        raise HTTPException(status_code=500, detail="Failed to process payment")
    
    print(f"Payment processed successfully for {payment.customer_id} in {ddb_time:.4f}s")
    return {
        "message": "Payment processed successfully", 
        "transaction_id": payment.transaction_id,
        "processing_time_ms": ddb_time * 1000
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
        "message": "Analytics Dashboard",
        "total_customers_tracked": len(user_analytics_data),
        "total_transactions_analyzed": len(request_analytics),
        "memory_objects_created": len(temp_analysis),
        "status": "growing_rapidly",
        "note": "Analytics data is accumulating for better fraud detection!"
    }


@app.post("/customers/create")
def create_customer(customer: Customer):
    success = store_customer(
        customer.customer_id,
        customer.name,
        customer.email,
        customer.account_status
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to create customer record")
    
    return {
        "message": "Customer created successfully",
        "customer_id": customer.customer_id
    }

@app.get("/customers/{customer_id}")
def get_customer_info(customer_id: str):
    result = get_customer(customer_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.get("/payments/history/{customer_id}")
def get_payments(customer_id: str, limit: Optional[int] = Query(10, ge=1, le=100)):
    result = get_payment_history(customer_id, limit)
    if result and "error" in result[0]:
        raise HTTPException(status_code=500, detail=result[0]["error"])
    return result

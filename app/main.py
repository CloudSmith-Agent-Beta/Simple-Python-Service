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

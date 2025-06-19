import boto3
import os
import time
import json
from datetime import datetime
from botocore.exceptions import ClientError
from typing import Dict, List, Optional, Any

DDB_TABLE_NAME = os.environ.get("DDB_TABLE_NAME")
DDB_REGION = os.environ.get("AWS_REGION", "us-west-2")

dynamodb = boto3.resource("dynamodb", region_name=DDB_REGION)
table = dynamodb.Table(DDB_TABLE_NAME)

# Initialize CloudWatch client for throttling metrics
cloudwatch = boto3.client('cloudwatch', region_name=DDB_REGION)

def store_payment(customer_id: str, amount: float, payment_method: str, 
                 transaction_id: Optional[str] = None) -> bool:
    """Store a payment record in DynamoDB"""
    max_retries = 3
    retry_count = 0
    
    # Generate transaction ID if not provided
    if not transaction_id:
        transaction_id = f"txn-{int(time.time())}-{customer_id}"
    
    # Create timestamp
    timestamp = datetime.utcnow().isoformat()
    
    while retry_count < max_retries:
        try:
            table.put_item(Item={
                "pk": f"CUSTOMER#{customer_id}",
                "sk": f"PAYMENT#{transaction_id}",
                "customer_id": customer_id,
                "amount": amount,
                "payment_method": payment_method,
                "transaction_id": transaction_id,
                "timestamp": timestamp,
                "record_type": "payment"
            })
            return True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code == 'ProvisionedThroughputExceededException':
                retry_count += 1
                print(f"[DynamoDB THROTTLED] Attempt {retry_count}/{max_retries} for {customer_id}")
                
                # Record throttling event in CloudWatch
                try:
                    cloudwatch.put_metric_data(
                        Namespace='PaymentServiceApplication',
                        MetricData=[
                            {
                                'MetricName': 'DynamoDBThrottling',
                                'Dimensions': [
                                    {
                                        'Name': 'TableName',
                                        'Value': DDB_TABLE_NAME
                                    }
                                ],
                                'Value': 1,
                                'Unit': 'Count'
                            },
                        ]
                    )
                except Exception as metric_error:
                    print(f"Failed to publish throttling metric: {str(metric_error)}")
                
                if retry_count < max_retries:
                    # Exponential backoff
                    backoff_time = 0.1 * (2 ** retry_count)
                    print(f"Backing off for {backoff_time:.2f} seconds")
                    time.sleep(backoff_time)
                    continue
            
            print(f"[DynamoDB ERROR] {e.response['Error']['Code']}: {e.response['Error']['Message']}")
            return False
    
    return False

def store_customer(customer_id: str, name: str, email: Optional[str] = None, 
                  account_status: str = "active") -> bool:
    """Store customer information in DynamoDB"""
    try:
        table.put_item(Item={
            "pk": f"CUSTOMER#{customer_id}",
            "sk": "PROFILE",
            "customer_id": customer_id,
            "name": name,
            "email": email,
            "account_status": account_status,
            "record_type": "customer"
        })
        return True
    except ClientError as e:
        print(f"[DynamoDB ERROR] {e.response['Error']['Message']}")
        return False

def get_customer(customer_id: str) -> Dict[str, Any]:
    """Retrieve customer information from DynamoDB"""
    try:
        response = table.get_item(Key={
            "pk": f"CUSTOMER#{customer_id}",
            "sk": "PROFILE"
        })
        item = response.get("Item", {})
        if not item:
            return {"error": "Customer not found"}
        
        # Clean up the response
        if "pk" in item:
            del item["pk"]
        if "sk" in item:
            del item["sk"]
        if "record_type" in item:
            del item["record_type"]
            
        return item
    except ClientError as e:
        print(f"[DynamoDB ERROR] {e.response['Error']['Message']}")
        return {"error": "Failed to read from DynamoDB"}

def get_payment_history(customer_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Retrieve payment history for a customer from DynamoDB"""
    try:
        response = table.query(
            KeyConditionExpression="pk = :pk AND begins_with(sk, :payment)",
            ExpressionAttributeValues={
                ":pk": f"CUSTOMER#{customer_id}",
                ":payment": "PAYMENT#"
            },
            Limit=limit,
            ScanIndexForward=False  # Sort in descending order (newest first)
        )
        
        items = response.get("Items", [])
        # Clean up the response
        for item in items:
            if "pk" in item:
                del item["pk"]
            if "sk" in item:
                del item["sk"]
            if "record_type" in item:
                del item["record_type"]
                
        return items
    except ClientError as e:
        print(f"[DynamoDB ERROR] {e.response['Error']['Message']}")
        return [{"error": "Failed to retrieve payment history"}]
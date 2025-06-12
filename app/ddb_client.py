import boto3
import os
import time
from botocore.exceptions import ClientError

DDB_TABLE_NAME = os.environ.get("DDB_TABLE_NAME")
DDB_REGION = os.environ.get("AWS_REGION", "us-west-2")

dynamodb = boto3.resource("dynamodb", region_name=DDB_REGION)
table = dynamodb.Table(DDB_TABLE_NAME)

# Initialize CloudWatch client for throttling metrics
cloudwatch = boto3.client('cloudwatch', region_name=DDB_REGION)

def write_to_dynamodb(user_id: str, value: str) -> bool:
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            table.put_item(Item={"user_id": user_id, "value": value})
            return True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code == 'ProvisionedThroughputExceededException':
                retry_count += 1
                print(f"[DynamoDB THROTTLED] Attempt {retry_count}/{max_retries} for {user_id}")
                
                # Record throttling event in CloudWatch
                try:
                    cloudwatch.put_metric_data(
                        Namespace='SampleMicroServiceApplication',
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

def read_from_dynamodb(user_id: str) -> dict:
    try:
        response = table.get_item(Key={"user_id": user_id})
        return response.get("Item", {"error": "Item not found"})
    except ClientError as e:
        print(f"[DynamoDB ERROR] {e.response['Error']['Message']}")
        return {"error": "Failed to read from DynamoDB"}

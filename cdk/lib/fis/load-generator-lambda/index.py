import os
import time
import requests
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
ENDPOINT = os.environ["ENDPOINT"]  # e.g. http://elb.amazonaws.com/write

def handler(event, context):
    logger.info(f"Starting load generation to endpoint: {ENDPOINT}")
    logger.info(f"Event received: {event}")
    print(f"Starting load generation to endpoint: {ENDPOINT}")
    for i in range(1000):  # simulate high write volume
        payload = {"user_id": f"user-{i}", "value": "stress"}
        try:
            response = requests.post(ENDPOINT, json=payload, timeout=1)
            print(f"[{i}] Status: {response.status_code}")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(0.05)  # throttle a little between writes
        
    logger.info("Load generation complete")
    return {"status": "complete", "requests_sent": 10}
"""CampusVoice: start_pipeline Lambda Function.

Triggered by S3 ObjectCreated on raw/uploads/*.csv.
Generates a unique batch_id (YYYYMMDDTHHMMSS-<6 hex>),
and starts the Step Functions state machine with the batch execution.
"""

import json
import os
import secrets
import urllib.parse
from datetime import datetime, timezone
import boto3

sfn_client = boto3.client("stepfunctions")
STATE_MACHINE_ARN = os.environ.get("STATE_MACHINE_ARN")


def lambda_handler(event, context):
    print("Received S3 event to initiate pipeline execution.")
    
    # Process S3 event records
    records = event.get("Records", [])
    if not records:
        print("No S3 records found in event.")
        return {"statusCode": 400, "body": "No records in event"}

    record = records[0]
    s3_info = record.get("s3", {})
    bucket_name = s3_info.get("bucket", {}).get("name")
    raw_key = s3_info.get("object", {}).get("key", "")
    object_key = urllib.parse.unquote_plus(raw_key)

    if not object_key.endswith(".csv"):
        print(f"Skipping non-CSV object: {object_key}")
        return {"statusCode": 200, "body": f"Skipped non-csv file: {object_key}"}

    # Generate batch_id per contract: YYYYMMDDTHHMMSS-<6 hex>
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    hex_suffix = secrets.token_hex(3)
    batch_id = f"{timestamp_str}-{hex_suffix}"

    execution_name = f"cv-{batch_id}"

    payload = {
        "bucket": bucket_name,
        "key": object_key,
        "batch_id": batch_id
    }

    print(f"Starting state machine execution: {execution_name} for batch: {batch_id}")
    response = sfn_client.start_execution(
        stateMachineArn=STATE_MACHINE_ARN,
        name=execution_name,
        input=json.dumps(payload)
    )

    return {
        "statusCode": 200,
        "batch_id": batch_id,
        "executionArn": response["executionArn"]
    }

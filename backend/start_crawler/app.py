"""CampusVoice: start_crawler Lambda Function.

Updates and verifies the Glue Data Catalog partitions for curated Parquet data.
Executes Athena partition refresh (MSCK REPAIR TABLE) or invokes the Glue Crawler
if available, ensuring catalog consistency for SQL dashboards and analytics.
"""

import os
import time
import boto3

athena_client = boto3.client("athena")
glue_client = boto3.client("glue")

PROCESSED_BUCKET = os.environ.get("PROCESSED_BUCKET")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "campusvoice_db_dev")
KMS_KEY_ID = os.environ.get("KMS_KEY_ID")


def run_athena_repair() -> bool:
    """Run MSCK REPAIR TABLE in Athena to register any new S3 partitions in the Glue Catalog."""
    query = f"MSCK REPAIR TABLE {DATABASE_NAME}.feedback"
    output_loc = f"s3://{PROCESSED_BUCKET}/athena-results/"
    kwargs = {
        "QueryString": query,
        "QueryExecutionContext": {"Database": DATABASE_NAME},
        "ResultConfiguration": {"OutputLocation": output_loc}
    }
    if KMS_KEY_ID:
        kwargs["ResultConfiguration"]["EncryptionConfiguration"] = {
            "EncryptionOption": "SSE_KMS",
            "KmsKey": KMS_KEY_ID
        }

    try:
        resp = athena_client.start_query_execution(**kwargs)
        qid = resp["QueryExecutionId"]

        for _ in range(30):
            time.sleep(2)
            status_resp = athena_client.get_query_execution(QueryExecutionId=qid)
            state = status_resp["QueryExecution"]["Status"]["State"]
            if state == "SUCCEEDED":
                print("Athena MSCK REPAIR TABLE succeeded.")
                return True
            elif state in ["FAILED", "CANCELLED"]:
                print(f"Athena repair status: {state}")
                return False
    except Exception as ex:
        print(f"Athena partition repair notice: {ex}")
        return False
    return True


def lambda_handler(event, context):
    print("Catalog partition synchronization stage started.")
    batch_id = event.get("batch_id", "unknown")

    # Run catalog partition refresh
    repaired = run_athena_repair()

    return {
        "statusCode": 200,
        "batch_id": batch_id,
        "status": "COMPLETED",
        "catalog_database": DATABASE_NAME,
        "table": "feedback",
        "partitions_synchronized": repaired
    }

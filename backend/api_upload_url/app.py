"""CampusVoice: api_upload_url Lambda Function.

Admin-only endpoint that generates a secure, presigned S3 PUT URL for uploading
student feedback CSV files into the raw bucket prefix raw/uploads/<filename>.
Enforces 15-minute expiration and Content-Type: text/csv.
Restricted strictly to the Cognito Admin group.
"""

import json
import os
import re
import boto3
from botocore.config import Config

s3_client = boto3.client(
    "s3",
    region_name="us-east-1",
    config=Config(signature_version="s3v4")
)

RAW_BUCKET = os.environ.get("RAW_BUCKET")

CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With"
}


def is_admin_user(event: dict) -> bool:
    """Extract and verify Admin group membership from Cognito JWT claims."""
    claims = event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})
    groups = claims.get("cognito:groups", [])
    if isinstance(groups, str):
        # Could be formatted as "[Admin]" or "Admin"
        groups = groups.strip("[]").replace('"', '').replace("'", '').split(",")
        groups = [g.strip() for g in groups]
    return "Admin" in groups


def lambda_handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method") or event.get("httpMethod", "POST")
    if method == "OPTIONS":
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": json.dumps({"status": "ok"})}

    # Enforce RBAC: Admin only
    if not is_admin_user(event):
        return {
            "statusCode": 403,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": "Forbidden: Admin privileges required to generate upload URLs."})
        }

    try:
        body = json.loads(event.get("body") or "{}")
    except Exception:
        body = {}

    filename = body.get("filename", "feedback_upload.csv").strip()
    if not filename:
        filename = "feedback_upload.csv"

    # Sanitize filename
    clean_name = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", filename)
    if not clean_name.lower().endswith(".csv"):
        clean_name += ".csv"

    s3_key = f"uploads/{clean_name}"
    expiry_seconds = 900  # 15 minutes

    try:
        presigned_url = s3_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": RAW_BUCKET,
                "Key": s3_key,
                "ContentType": "text/csv"
            },
            ExpiresIn=expiry_seconds
        )

        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps({
                "upload_url": presigned_url,
                "key": s3_key,
                "bucket": RAW_BUCKET,
                "expires_in": expiry_seconds,
                "content_type": "text/csv"
            })
        }

    except Exception as ex:
        print(f"Error generating presigned upload URL: {ex}")
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": f"Failed to generate upload URL: {str(ex)}"})
        }

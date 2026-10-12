"""CampusVoice: sign_manifest Lambda Function.

Builds a cryptographic batch manifest ({batch_id, row_count, curated_prefix, sha256}),
computes its SHA-256 digest, and digitally signs the digest using the KMS asymmetric
signing key (RSASSA_PKCS1_V1_5_SHA_256).
Persists the manifest JSON and detached .sig file to processed/manifests/.
"""

import base64
import hashlib
import json
import os
import boto3

s3_client = boto3.client("s3")
kms_client = boto3.client("kms")

PROCESSED_BUCKET = os.environ.get("PROCESSED_BUCKET")
SIGN_KEY_ID = os.environ.get("SIGN_KEY_ID")


def lambda_handler(event, context):
    print("Initiating batch manifest cryptographic signing.")
    batch_id = event.get("batch_id", "unknown-batch")
    curated_prefix = f"curated/"

    # Estimate or count rows from S3 curated objects or previous step metadata
    row_count = event.get("record_count", 0)

    # 1. Build canonical manifest JSON
    manifest_data = {
        "batch_id": batch_id,
        "row_count": row_count,
        "curated_prefix": f"s3://{PROCESSED_BUCKET}/{curated_prefix}",
        "timestamp": event.get("timestamp") or context.aws_request_id
    }
    manifest_str = json.dumps(manifest_data, sort_keys=True)
    manifest_bytes = manifest_str.encode("utf-8")

    # 2. Compute SHA-256 digest
    digest = hashlib.sha256(manifest_bytes).digest()
    manifest_data["sha256"] = hashlib.sha256(manifest_bytes).hexdigest()
    final_manifest_json = json.dumps(manifest_data, indent=2, sort_keys=True)

    print(f"Signing manifest for batch: {batch_id} using KMS asymmetric key.")

    # 3. Sign the SHA-256 digest with the asymmetric KMS key
    # RSASSA_PKCS1_V1_5_SHA_256 with MessageType='DIGEST'
    sign_response = kms_client.sign(
        KeyId=SIGN_KEY_ID,
        Message=digest,
        MessageType="DIGEST",
        SigningAlgorithm="RSASSA_PKCS1_V1_5_SHA_256"
    )
    raw_signature = sign_response["Signature"]

    # 4. Save manifest JSON and detached signature (.sig) to S3
    manifest_key = f"manifests/{batch_id}.json"
    sig_key = f"manifests/{batch_id}.sig"

    s3_client.put_object(
        Bucket=PROCESSED_BUCKET,
        Key=manifest_key,
        Body=final_manifest_json.encode("utf-8"),
        ContentType="application/json"
    )

    s3_client.put_object(
        Bucket=PROCESSED_BUCKET,
        Key=sig_key,
        Body=raw_signature,
        ContentType="application/octet-stream"
    )

    print(f"Manifest written to s3://{PROCESSED_BUCKET}/{manifest_key}")
    print(f"Detached signature written to s3://{PROCESSED_BUCKET}/{sig_key}")

    return {
        "statusCode": 200,
        "batch_id": batch_id,
        "manifest_path": f"s3://{PROCESSED_BUCKET}/{manifest_key}",
        "signature_path": f"s3://{PROCESSED_BUCKET}/{sig_key}",
        "sha256": manifest_data["sha256"],
        "signature_base64": base64.b64encode(raw_signature).decode("ascii")
    }

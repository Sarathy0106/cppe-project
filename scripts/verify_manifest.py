"""Verify CampusVoice batch manifest digital signature with AWS KMS."""
import hashlib
import json
from pathlib import Path
import boto3

s3 = boto3.client("s3")
kms = boto3.client("kms")

bucket = "campusvoice-processed-657878533694-dev"
prefix = "manifests/"

# 1. Find latest manifest in S3
resp = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
json_files = [obj["Key"] for obj in resp.get("Contents", []) if obj["Key"].endswith(".json")]

if not json_files:
    print("No manifests found in S3 bucket.")
    exit(1)

latest_manifest_key = sorted(json_files)[-1]
batch_id = Path(latest_manifest_key).stem
sig_key = f"manifests/{batch_id}.sig"

print(f"Verifying batch manifest: {batch_id}")

# 2. Download manifest JSON and detached .sig signature
manifest_bytes_raw = s3.get_object(Bucket=bucket, Key=latest_manifest_key)["Body"].read()
manifest_obj = json.loads(manifest_bytes_raw.decode("utf-8"))

sig_bytes = s3.get_object(Bucket=bucket, Key=sig_key)["Body"].read()

# 3. Reconstruct canonical manifest bytes for SHA-256 digest
canonical_data = {
    "batch_id": manifest_obj["batch_id"],
    "curated_prefix": manifest_obj["curated_prefix"],
    "row_count": manifest_obj["row_count"],
    "timestamp": manifest_obj["timestamp"]
}
canonical_bytes = json.dumps(canonical_data, sort_keys=True).encode("utf-8")
digest = hashlib.sha256(canonical_bytes).digest()

# Save binary files locally for terminal CLI verification
Path("digest.bin").write_bytes(digest)
Path("signature.bin").write_bytes(sig_bytes)

# 4. Verify via AWS KMS Asymmetric Key
res = kms.verify(
    KeyId="alias/campusvoice-sign",
    Message=digest,
    MessageType="DIGEST",
    Signature=sig_bytes,
    SigningAlgorithm="RSASSA_PKCS1_V1_5_SHA_256"
)

output = {
    "KeyId": res.get("KeyId"),
    "SignatureValid": res.get("SignatureValid"),
    "SigningAlgorithm": res.get("SigningAlgorithm")
}

print(json.dumps(output, indent=2))

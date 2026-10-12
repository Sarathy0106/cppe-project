#!/usr/bin/env bash
# ==============================================================================
# CampusVoice: Simulate Suspicious Activity & Security Threat Detection
# Wipro CPPE Module 4 (Cloud Security, Cryptography & Governance)
#
# Generates repeated AccessDenied API calls to trigger the CloudWatch Metric Filter
# and CloudWatch Alarm: campusvoice-access-denied-dev -> SNS Alerts Topic.
# ==============================================================================

set -uo pipefail

STAGE="${STAGE:-dev}"
REGION="${AWS_REGION:-us-east-1}"

echo "================================================================="
echo " CampusVoice: Simulating Suspicious Security Events"
echo " Target: Trigger CloudWatch AccessDenied Alarm & SNS Notification"
echo "================================================================="

ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
RAW_BUCKET="campusvoice-raw-${ACCOUNT_ID}-${STAGE}"
PROCESSED_BUCKET="campusvoice-processed-${ACCOUNT_ID}-${STAGE}"

echo "Current Caller Identity:"
aws sts get-caller-identity --output table

echo ""
echo "[Step 1/5] Attempting unauthorized S3 access to prohibited internal path..."
aws s3 cp "s3://${RAW_BUCKET}/system/secret-keys.pem" ./secret-keys.pem 2>&1 || true

echo ""
echo "[Step 2/5] Attempting unauthorized S3 deletion on curated Parquet data..."
aws s3 rm "s3://${PROCESSED_BUCKET}/curated/confidential-dump.parquet" 2>&1 || true

echo ""
echo "[Step 3/5] Attempting unauthorized KMS key decryption with dummy ciphertext..."
aws kms decrypt --ciphertext-blob "AQICAHg9M2..." --key-id "alias/campusvoice-data" 2>&1 || true

echo ""
echo "[Step 4/5] Attempting unauthorized S3 GetObject on non-existent admin audit log..."
aws s3api get-object --bucket "${RAW_BUCKET}" --key "admin-audit-private.log" ./temp.log 2>&1 || true

echo ""
echo "[Step 5/5] Attempting unauthorized KMS decrypt on manifest signing key..."
aws kms decrypt --ciphertext-blob "AQICAHg9M2..." --key-id "alias/campusvoice-sign" 2>&1 || true

echo ""
echo "================================================================="
echo " Suspicious events simulated successfully."
echo " CloudTrail will ingest events into LogGroup within 1-5 minutes."
echo " Metric Filter: CampusVoice/Security -> AccessDeniedCount"
echo " Alarm: campusvoice-access-denied-${STAGE} (Threshold >= 3)"
echo "================================================================="

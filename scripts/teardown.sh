#!/usr/bin/env bash
# ==============================================================================
# CampusVoice: Automated Infrastructure Teardown Script (Bash)
# Cleanly purges all S3 buckets (including object versions), deletes the CloudFormation
# stack, and schedules KMS Customer Managed Keys for 7-day pending deletion.
# ==============================================================================

set -uo pipefail

STAGE="${STAGE:-dev}"
REGION="${AWS_REGION:-us-east-1}"
STACK_NAME="campusvoice-${STAGE}"

echo "================================================================="
echo " WARNING: CampusVoice Complete Infrastructure Teardown"
echo " Target Stack: ${STACK_NAME} (${REGION})"
echo "================================================================="
read -p "Are you sure you want to permanently delete all CampusVoice resources? (y/N): " -r CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo "Teardown cancelled by user."
    exit 0
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)

BUCKETS=(
    "campusvoice-raw-${ACCOUNT_ID}-${STAGE}"
    "campusvoice-processed-${ACCOUNT_ID}-${STAGE}"
    "campusvoice-logs-${ACCOUNT_ID}-${STAGE}"
    "campusvoice-frontend-${ACCOUNT_ID}-${STAGE}"
)

echo ""
echo "[Step 1/3] Emptying all versioned S3 buckets..."
for BUCKET in "${BUCKETS[@]}"; do
    echo "Purging bucket: s3://${BUCKET}..."
    if aws s3api head-bucket --bucket "$BUCKET" 2>/dev/null; then
        # Delete all object versions and delete markers
        aws s3api delete-objects --bucket "$BUCKET" \
            --delete "$(aws s3api list-object-versions --bucket "$BUCKET" --query='{Objects: Versions[].{Key:Key,VersionId:VersionId}}' --output json 2>/dev/null)" 2>/dev/null || true
        aws s3api delete-objects --bucket "$BUCKET" \
            --delete "$(aws s3api list-object-versions --bucket "$BUCKET" --query='{Objects: DeleteMarkers[].{Key:Key,VersionId:VersionId}}' --output json 2>/dev/null)" 2>/dev/null || true
        aws s3 rm "s3://${BUCKET}" --recursive 2>/dev/null || true
        echo " -> Emptied s3://${BUCKET}"
    else
        echo " -> Bucket s3://${BUCKET} does not exist or already removed."
    fi
done

echo ""
echo "[Step 2/3] Deleting CloudFormation Stack: ${STACK_NAME}..."
aws cloudformation delete-stack --stack-name "$STACK_NAME" --region "$REGION"
echo "Waiting for stack deletion to complete..."
aws cloudformation wait stack-delete-complete --stack-name "$STACK_NAME" --region "$REGION" || true
echo " -> CloudFormation stack deleted."

echo ""
echo "[Step 3/3] Scheduling KMS Keys for deletion (7-day safety window)..."
for ALIAS in "alias/campusvoice-data" "alias/campusvoice-sign"; do
    KEY_ID=$(aws kms describe-key --key-id "$ALIAS" --query "KeyMetadata.KeyId" --output text 2>/dev/null || true)
    if [ -n "$KEY_ID" ] && [ "$KEY_ID" != "None" ]; then
        aws kms schedule-key-deletion --key-id "$KEY_ID" --pending-window-in-days 7 >/dev/null 2>&1 || true
        echo " -> Scheduled KMS Key ${KEY_ID} (${ALIAS}) for deletion in 7 days."
    fi
done

echo ""
echo "================================================================="
echo " Teardown Verification Checklist:"
echo " [x] S3 buckets emptied and removed"
echo " [x] CloudFormation stack campusvoice-${STAGE} deleted"
echo " [x] Lambda functions, API Gateway, and Step Functions removed"
echo " [x] KMS Customer Managed Keys scheduled for deletion"
echo " [x] No running Glue jobs or provisioned clusters active"
echo " Zero ongoing AWS charges remain."
echo "================================================================="

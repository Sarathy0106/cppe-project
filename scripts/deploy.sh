#!/usr/bin/env bash
set -euo pipefail

STAGE="${STAGE:-dev}"
REGION="${AWS_REGION:-us-east-1}"

echo "=============================================="
echo " CampusVoice: Building and Deploying SAM Stack"
echo "=============================================="

sam build
sam deploy --no-confirm-changeset

echo "Fetching CloudFormation stack outputs..."
STACK_NAME="campusvoice-${STAGE}"
FRONTEND_BUCKET=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" --output text)
API_URL=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='HttpApiUrl'].OutputValue" --output text)
USER_POOL_ID=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='UserPoolId'].OutputValue" --output text)
CLIENT_ID=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='UserPoolClientId'].OutputValue" --output text)

echo "Building Vue 3 Frontend..."
cd frontend
cat <<EOF > public/config.json
{
  "apiUrl": "${API_URL}",
  "userPoolId": "${USER_POOL_ID}",
  "clientId": "${CLIENT_ID}",
  "region": "${REGION}"
}
EOF

npm ci
npm run build

echo "Syncing frontend to S3: s3://${FRONTEND_BUCKET}..."
aws s3 sync dist/ "s3://${FRONTEND_BUCKET}" --delete

echo "Frontend deployment completed successfully."


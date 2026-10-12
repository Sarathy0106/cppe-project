# ==============================================================================
# CampusVoice: Simulate Suspicious Activity & Security Threat Detection (PowerShell)
# Wipro CPPE Module 4 (Cloud Security, Cryptography & Governance)
#
# Generates repeated AccessDenied API calls to trigger the CloudWatch Metric Filter
# and CloudWatch Alarm: campusvoice-access-denied-dev -> SNS Alerts Topic.
# ==============================================================================

$Stage = if ($env:STAGE) { $env:STAGE } else { "dev" }
$Region = if ($env:AWS_REGION) { $env:AWS_REGION } else { "us-east-1" }

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host " CampusVoice: Simulating Suspicious Security Events" -ForegroundColor Cyan
Write-Host " Target: Trigger CloudWatch AccessDenied Alarm & SNS Notification" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

$AccountId = (aws sts get-caller-identity --query "Account" --output text).Trim()
$RawBucket = "campusvoice-raw-$AccountId-$Stage"
$ProcessedBucket = "campusvoice-processed-$AccountId-$Stage"

Write-Host "Current Caller Identity:"
aws sts get-caller-identity --output table

Write-Host "`n[Step 1/5] Attempting unauthorized S3 access to prohibited internal path..." -ForegroundColor Yellow
aws s3 cp "s3://$RawBucket/system/secret-keys.pem" .\secret-keys.pem 2>&1 | Out-Null

Write-Host "`n[Step 2/5] Attempting unauthorized S3 deletion on curated Parquet data..." -ForegroundColor Yellow
aws s3 rm "s3://$ProcessedBucket/curated/confidential-dump.parquet" 2>&1 | Out-Null

Write-Host "`n[Step 3/5] Attempting unauthorized KMS key decryption with dummy ciphertext..." -ForegroundColor Yellow
aws kms decrypt --ciphertext-blob "AQICAHg9M2..." --key-id "alias/campusvoice-data" 2>&1 | Out-Null

Write-Host "`n[Step 4/5] Attempting unauthorized S3 GetObject on non-existent admin audit log..." -ForegroundColor Yellow
aws s3api get-object --bucket "$RawBucket" --key "admin-audit-private.log" .\temp.log 2>&1 | Out-Null

Write-Host "`n[Step 5/5] Attempting unauthorized KMS decrypt on manifest signing key..." -ForegroundColor Yellow
aws kms decrypt --ciphertext-blob "AQICAHg9M2..." --key-id "alias/campusvoice-sign" 2>&1 | Out-Null

Write-Host "`n=================================================================" -ForegroundColor Green
Write-Host " Suspicious events simulated successfully." -ForegroundColor Green
Write-Host " CloudTrail will ingest events into LogGroup within 1-5 minutes." -ForegroundColor Green
Write-Host " Metric Filter: CampusVoice/Security -> AccessDeniedCount" -ForegroundColor Green
Write-Host " Alarm: campusvoice-access-denied-$Stage (Threshold >= 3)" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green

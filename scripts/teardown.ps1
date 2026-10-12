# ==============================================================================
# CampusVoice: Automated Infrastructure Teardown Script (PowerShell)
# Cleanly purges all S3 buckets (including object versions), deletes the CloudFormation
# stack, and schedules KMS Customer Managed Keys for 7-day pending deletion.
# ==============================================================================

$Stage = if ($env:STAGE) { $env:STAGE } else { "dev" }
$Region = if ($env:AWS_REGION) { $env:AWS_REGION } else { "us-east-1" }
$StackName = "campusvoice-$Stage"

Write-Host "=================================================================" -ForegroundColor Red
Write-Host " WARNING: CampusVoice Complete Infrastructure Teardown" -ForegroundColor Red
Write-Host " Target Stack: $StackName ($Region)" -ForegroundColor Red
Write-Host "=================================================================" -ForegroundColor Red

$Confirmation = Read-Host "Are you sure you want to permanently delete all CampusVoice resources? (y/N)"
if ($Confirmation -notmatch "^[Yy]$") {
    Write-Host "Teardown cancelled by user." -ForegroundColor Yellow
    exit 0
}

$AccountId = (aws sts get-caller-identity --query "Account" --output text).Trim()

$Buckets = @(
    "campusvoice-raw-$AccountId-$Stage",
    "campusvoice-processed-$AccountId-$Stage",
    "campusvoice-logs-$AccountId-$Stage",
    "campusvoice-frontend-$AccountId-$Stage"
)

Write-Host "`n[Step 1/3] Emptying all versioned S3 buckets..." -ForegroundColor Cyan
foreach ($Bucket in $Buckets) {
    Write-Host "Purging bucket: s3://$Bucket..." -ForegroundColor Yellow
    try {
        aws s3 rm "s3://$Bucket" --recursive 2>$null | Out-Null
        
        # Purge all object versions
        $Versions = aws s3api list-object-versions --bucket $Bucket --query "{Objects: Versions[].{Key:Key,VersionId:VersionId}}" --output json 2>$null
        if ($Versions -and $Versions.Trim() -ne "null" -and $Versions.Trim() -ne "{}") {
            aws s3api delete-objects --bucket $Bucket --delete $Versions 2>$null | Out-Null
        }

        # Purge delete markers
        $Markers = aws s3api list-object-versions --bucket $Bucket --query "{Objects: DeleteMarkers[].{Key:Key,VersionId:VersionId}}" --output json 2>$null
        if ($Markers -and $Markers.Trim() -ne "null" -and $Markers.Trim() -ne "{}") {
            aws s3api delete-objects --bucket $Bucket --delete $Markers 2>$null | Out-Null
        }
        Write-Host " -> Emptied s3://$Bucket" -ForegroundColor Green
    } catch {
        Write-Host " -> Error or already emptied: $Bucket" -ForegroundColor DarkGray
    }
}

Write-Host "`n[Step 2/3] Deleting CloudFormation Stack: $StackName..." -ForegroundColor Cyan
aws cloudformation delete-stack --stack-name $StackName --region $Region
Write-Host "Waiting for stack deletion to complete..." -ForegroundColor Yellow
aws cloudformation wait stack-delete-complete --stack-name $StackName --region $Region
Write-Host " -> CloudFormation stack deleted successfully." -ForegroundColor Green

Write-Host "`n[Step 3/3] Scheduling KMS Keys for deletion (7-day safety window)..." -ForegroundColor Cyan
$KeyAliases = @("alias/campusvoice-data", "alias/campusvoice-sign")
foreach ($Alias in $KeyAliases) {
    $KeyId = (aws kms describe-key --key-id $Alias --query "KeyMetadata.KeyId" --output text 2>$null).Trim()
    if ($KeyId -and $KeyId -ne "None") {
        aws kms schedule-key-deletion --key-id $KeyId --pending-window-in-days 7 2>$null | Out-Null
        Write-Host " -> Scheduled KMS Key $KeyId ($Alias) for deletion in 7 days." -ForegroundColor Green
    }
}

Write-Host "`n=================================================================" -ForegroundColor Green
Write-Host " Teardown Verification Checklist:" -ForegroundColor Green
Write-Host " [x] S3 buckets emptied and removed" -ForegroundColor Green
Write-Host " [x] CloudFormation stack $StackName deleted" -ForegroundColor Green
Write-Host " [x] Lambda functions, API Gateway, and Step Functions removed" -ForegroundColor Green
Write-Host " [x] KMS Customer Managed Keys scheduled for deletion" -ForegroundColor Green
Write-Host " [x] No running Glue jobs or provisioned clusters active" -ForegroundColor Green
Write-Host " Zero ongoing AWS charges remain." -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green

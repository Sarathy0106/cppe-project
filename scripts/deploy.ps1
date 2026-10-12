# CampusVoice: Windows PowerShell deployment script
$ErrorActionPreference = "Stop"

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host " CampusVoice: Building and Deploying SAM Stack" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan

# Refresh path if needed
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

sam build
sam deploy --no-confirm-changeset

Write-Host "SAM deployment completed successfully." -ForegroundColor Green

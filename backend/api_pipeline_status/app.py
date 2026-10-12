"""CampusVoice: api_pipeline_status Lambda Function.

Admin-only endpoint that queries Step Functions state machine execution history
and stage statuses for data pipeline monitoring.
Restricted strictly to the Cognito Admin group.
"""

import json
import os
from datetime import datetime
import boto3

sfn_client = boto3.client("stepfunctions")

STATE_MACHINE_ARN = os.environ.get("STATE_MACHINE_ARN")

CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With"
}


def is_admin_user(event: dict) -> bool:
    """Extract and verify Admin group membership from Cognito JWT claims."""
    claims = event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})
    groups = claims.get("cognito:groups", [])
    if isinstance(groups, str):
        groups = groups.strip("[]").replace('"', '').replace("'", '').split(",")
        groups = [g.strip() for g in groups]
    return "Admin" in groups


def format_dt(dt) -> str:
    if isinstance(dt, datetime):
        return dt.isoformat()
    return str(dt) if dt else None


def lambda_handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method") or event.get("httpMethod", "GET")
    if method == "OPTIONS":
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": json.dumps({"status": "ok"})}

    # Enforce RBAC: Admin only
    if not is_admin_user(event):
        return {
            "statusCode": 403,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": "Forbidden: Admin privileges required to access pipeline status."})
        }

    params = event.get("queryStringParameters") or {}
    exec_arn = params.get("execution_arn")

    try:
        if exec_arn:
            # Describe specific execution
            details = sfn_client.describe_execution(executionArn=exec_arn)
            output_data = {}
            if details.get("output"):
                try:
                    output_data = json.loads(details["output"])
                except Exception:
                    output_data = details["output"]

            return {
                "statusCode": 200,
                "headers": CORS_HEADERS,
                "body": json.dumps({
                    "execution_arn": details.get("executionArn"),
                    "name": details.get("name"),
                    "status": details.get("status"),
                    "start_date": format_dt(details.get("startDate")),
                    "stop_date": format_dt(details.get("stopDate")),
                    "output": output_data
                })
            }
        else:
            # List recent executions
            resp = sfn_client.list_executions(
                stateMachineArn=STATE_MACHINE_ARN,
                maxResults=10
            )
            executions = []
            for item in resp.get("executions", []):
                executions.append({
                    "name": item.get("name"),
                    "status": item.get("status"),
                    "execution_arn": item.get("executionArn"),
                    "start_date": format_dt(item.get("startDate")),
                    "stop_date": format_dt(item.get("stopDate"))
                })

            return {
                "statusCode": 200,
                "headers": CORS_HEADERS,
                "body": json.dumps({
                    "state_machine_arn": STATE_MACHINE_ARN,
                    "executions": executions
                })
            }

    except Exception as ex:
        print(f"Error fetching pipeline status: {ex}")
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": f"Failed to retrieve pipeline status: {str(ex)}"})
        }

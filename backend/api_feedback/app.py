"""CampusVoice: api_feedback Lambda Function.

Provides a safe, parameterized feedback explorer querying curated records
from Amazon Athena. Enforces strict input allow-lists on all filter parameters
to completely prevent SQL injection vulnerabilities.
"""

import json
import os
import re
from athena import execute_athena_query

DATABASE_NAME = os.environ.get("DATABASE_NAME", "campusvoice_db_dev")
WORKGROUP_NAME = os.environ.get("ATHENA_WORKGROUP", "campusvoice-analytics-dev")

VALID_DEPTS = {"CSE", "ECE", "EEE", "MECH", "CIVIL", "IT"}
VALID_CATEGORIES = {"ADMIN", "CANTEEN", "FACULTY", "HOSTEL", "INFRASTRUCTURE", "LABS", "OTHER"}
VALID_SENTIMENTS = {"POSITIVE", "NEGATIVE", "NEUTRAL", "MIXED"}
MONTH_PATTERN = re.compile(r"^\d{4}-\d{2}$")

CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With"
}


def lambda_handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method") or event.get("httpMethod", "GET")
    if method == "OPTIONS":
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": json.dumps({"status": "ok"})}

    params = event.get("queryStringParameters") or {}

    dept = params.get("department", "").strip().upper()
    cat = params.get("category", "").strip().upper()
    sent = params.get("sentiment", "").strip().upper()
    month = params.get("month", "").strip()
    limit_str = params.get("limit", "50").strip()
    offset_str = params.get("offset", "0").strip()

    # Validate inputs
    clauses = ["1=1"]

    if dept:
        if dept not in VALID_DEPTS:
            return {
                "statusCode": 400,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": f"Invalid department '{dept}'. Allowed: {sorted(list(VALID_DEPTS))}"})
            }
        clauses.append(f"department = '{dept}'")

    if cat:
        if cat not in VALID_CATEGORIES:
            return {
                "statusCode": 400,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": f"Invalid category '{cat}'. Allowed: {sorted(list(VALID_CATEGORIES))}"})
            }
        clauses.append(f"category = '{cat}'")

    if sent:
        if sent not in VALID_SENTIMENTS:
            return {
                "statusCode": 400,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": f"Invalid sentiment '{sent}'. Allowed: {sorted(list(VALID_SENTIMENTS))}"})
            }
        clauses.append(f"sentiment = '{sent}'")

    if month:
        if not MONTH_PATTERN.match(month):
            return {
                "statusCode": 400,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": f"Invalid month '{month}'. Expected format: YYYY-MM (e.g., 2026-05)"})
            }
        clauses.append(f"month = '{month}'")

    try:
        limit = min(max(int(limit_str), 1), 100)
    except ValueError:
        limit = 50

    try:
        offset = max(int(offset_str), 0)
    except ValueError:
        offset = 0

    where_sql = " AND ".join(clauses)
    pagination_sql = f"LIMIT {limit}" if offset == 0 else f"OFFSET {offset} LIMIT {limit}"

    query = f"""
        SELECT 
            feedback_id, department, year, feedback_text, feedback_date,
            sentiment, category, category_confidence, pii_count, month
        FROM {DATABASE_NAME}.feedback
        WHERE {where_sql}
        ORDER BY feedback_date DESC
        {pagination_sql};
    """

    try:
        results = execute_athena_query(query, database=DATABASE_NAME, workgroup=WORKGROUP_NAME)
        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps({
                "items": results,
                "count": len(results),
                "limit": limit,
                "offset": offset,
                "filters": {
                    "department": dept or None,
                    "category": cat or None,
                    "sentiment": sent or None,
                    "month": month or None
                }
            })
        }
    except Exception as ex:
        print(f"Error executing feedback query: {ex}")
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": f"Athena query failed: {str(ex)}"})
        }

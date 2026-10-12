"""CampusVoice: api_stats Lambda Function.

Executes allow-listed canned Athena SQL queries for analytics dashboards and reports.
Implements an in-memory cache with 60-second TTL to deliver sub-100ms response times
on repeated calls without invoking additional Athena scans.
"""

import json
import os
import time
from athena import execute_athena_query

DATABASE_NAME = os.environ.get("DATABASE_NAME", "campusvoice_db_dev")
WORKGROUP_NAME = os.environ.get("ATHENA_WORKGROUP", "campusvoice-analytics-dev")

# In-memory TTL cache (lives for the life of the container)
CACHE = {}
CACHE_TTL_SECONDS = 60

CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With"
}

# Strict allow-list of canned SQL queries (no arbitrary user input concatenation)
QUERIES = {
    "kpis": f"""
        SELECT 
            count(*) as total_feedback,
            round(100.0 * sum(case when sentiment = 'POSITIVE' then 1 else 0 end) / count(*), 1) as pct_positive,
            round(100.0 * sum(case when sentiment = 'NEGATIVE' then 1 else 0 end) / count(*), 1) as pct_negative,
            count(distinct department) as department_count,
            coalesce(sum(pii_count), 0) as total_pii_masked
        FROM {DATABASE_NAME}.feedback;
    """,

    "sentiment_by_department": f"""
        SELECT 
            department,
            sentiment,
            count(*) as count
        FROM {DATABASE_NAME}.feedback
        GROUP BY department, sentiment
        ORDER BY department, sentiment;
    """,

    "category_counts": f"""
        SELECT 
            category,
            count(*) as count,
            round(avg(category_confidence), 3) as avg_confidence
        FROM {DATABASE_NAME}.feedback
        GROUP BY category
        ORDER BY count DESC;
    """,

    "monthly_trend": f"""
        SELECT 
            month,
            count(*) as total_count,
            sum(case when sentiment = 'NEGATIVE' then 1 else 0 end) as negative_count,
            round(100.0 * sum(case when sentiment = 'NEGATIVE' then 1 else 0 end) / count(*), 1) as negative_share,
            coalesce(sum(pii_count), 0) as pii_leak_attempts
        FROM {DATABASE_NAME}.feedback
        GROUP BY month
        ORDER BY month ASC;
    """,

    "top_complaints": f"""
        SELECT 
            category,
            department,
            count(*) as complaint_count
        FROM {DATABASE_NAME}.feedback
        WHERE sentiment = 'NEGATIVE'
        GROUP BY category, department
        ORDER BY complaint_count DESC
        LIMIT 10;
    """,

    "pii_trends": f"""
        SELECT 
            month,
            sum(pii_count) as pii_attempts,
            count(case when pii_count > 0 then 1 end) as feedback_with_pii
        FROM {DATABASE_NAME}.feedback
        GROUP BY month
        ORDER BY month ASC;
    """
}


def lambda_handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method") or event.get("httpMethod", "GET")
    if method == "OPTIONS":
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": json.dumps({"status": "ok"})}

    params = event.get("queryStringParameters") or {}
    query_type = params.get("type", "kpis").lower().strip()

    if query_type not in QUERIES:
        allowed = list(QUERIES.keys())
        return {
            "statusCode": 400,
            "headers": CORS_HEADERS,
            "body": json.dumps({
                "error": f"Invalid query type '{query_type}'. Allowed types: {allowed}"
            })
        }

    now = time.time()
    cache_entry = CACHE.get(query_type)

    # Check cache hit
    if cache_entry and (now - cache_entry["timestamp"]) < CACHE_TTL_SECONDS:
        cached_data = cache_entry["data"]
        headers = dict(CORS_HEADERS)
        headers["X-Cache"] = "HIT"
        headers["X-Cache-Age"] = str(int(now - cache_entry["timestamp"]))
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({
                "type": query_type,
                "cached": True,
                "data": cached_data
            })
        }

    # Execute canned query on Athena
    sql = QUERIES[query_type]
    try:
        t0 = time.time()
        results = execute_athena_query(sql, database=DATABASE_NAME, workgroup=WORKGROUP_NAME)
        duration_ms = round((time.time() - t0) * 1000, 2)

        # Store in cache
        CACHE[query_type] = {
            "timestamp": now,
            "data": results
        }

        headers = dict(CORS_HEADERS)
        headers["X-Cache"] = "MISS"
        headers["X-Query-Time-Ms"] = str(duration_ms)

        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({
                "type": query_type,
                "cached": False,
                "query_time_ms": duration_ms,
                "data": results
            })
        }

    except Exception as ex:
        print(f"Error executing stats query '{query_type}': {ex}")
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": f"Athena query failed: {str(ex)}"})
        }

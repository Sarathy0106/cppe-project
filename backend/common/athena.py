"""CampusVoice: Shared Athena Query Helper.

Provides reusable utilities for executing, polling, and formatting Athena SQL queries
against the Glue Data Catalog data lake with timeout safeguards and error handling.
"""

import logging
import os
import time

import boto3

athena_client = boto3.client("athena")
logger = logging.getLogger(__name__)

PROCESSED_BUCKET = os.environ.get("PROCESSED_BUCKET")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "campusvoice_db_dev")
WORKGROUP_NAME = os.environ.get("ATHENA_WORKGROUP", "primary")


def execute_athena_query(
    query: str,
    database: str | None = None,
    workgroup: str | None = None,
    timeout_sec: int = 30,
) -> list[dict]:
    """Execute Athena SQL query, poll for completion, and return results as list of dicts.

    Args:
        query: SQL query string
        database: Glue Catalog database name
        workgroup: Athena workgroup name (enforcing byte-scan cutoff)
        timeout_sec: Maximum wait duration before timeout

    Returns:
        List of dictionaries where keys are column names and values are typed entries.
    """
    db = database or DATABASE_NAME
    wg = workgroup or WORKGROUP_NAME

    kwargs = {
        "QueryString": query,
        "QueryExecutionContext": {"Database": db},
        "WorkGroup": wg
    }

    resp = athena_client.start_query_execution(**kwargs)
    qid = resp["QueryExecutionId"]

    # Poll with backoff
    start_time = time.time()
    backoff = 0.5

    while (time.time() - start_time) < timeout_sec:
        time.sleep(backoff)
        status_resp = athena_client.get_query_execution(QueryExecutionId=qid)
        status_obj = status_resp["QueryExecution"]["Status"]
        state = status_obj["State"]

        if state == "SUCCEEDED":
            return fetch_query_results(qid)
        elif state in ("FAILED", "CANCELLED"):
            reason = status_obj.get("StateChangeReason", "Unknown error")
            raise RuntimeError(f"Athena query failed ({state}): {reason}")

        backoff = min(backoff * 1.5, 2.0)

    # Cancel if timed out
    try:
        athena_client.stop_query_execution(QueryExecutionId=qid)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not stop timed out Athena query %s: %s", qid, exc)
    raise TimeoutError(f"Athena query timed out after {timeout_sec}s (QID: {qid})")


def fetch_query_results(qid: str) -> list[dict]:
    """Fetch and format Athena result set into a list of row dictionaries."""
    paginator = athena_client.get_paginator("get_query_results")
    rows = []
    headers = []
    types = []

    for page in paginator.paginate(QueryExecutionId=qid):
        result_set = page.get("ResultSet", {})
        metadata = result_set.get("ResultSetMetadata", {}).get("ColumnInfo", [])

        if not headers and metadata:
            headers = [col["Name"] for col in metadata]
            types = [col.get("Type", "varchar").lower() for col in metadata]

        raw_rows = result_set.get("Rows", [])
        start_idx = 1 if not rows and raw_rows else 0

        for r in raw_rows[start_idx:]:
            data_cells = r.get("Data", [])
            row_dict = {}
            for i, cell in enumerate(data_cells):
                col_name = headers[i] if i < len(headers) else f"col_{i}"
                col_type = types[i] if i < len(types) else "varchar"
                val = cell.get("VarCharValue")

                # Type cast
                if val is None:
                    row_dict[col_name] = None
                elif col_type in ("integer", "int", "smallint", "tinyint", "bigint"):
                    try:
                        row_dict[col_name] = int(val)
                    except ValueError:
                        row_dict[col_name] = val
                elif col_type in ("double", "float", "decimal", "real"):
                    try:
                        row_dict[col_name] = float(val)
                    except ValueError:
                        row_dict[col_name] = val
                elif col_type == "boolean":
                    row_dict[col_name] = val.lower() == "true"
                else:
                    row_dict[col_name] = val

            rows.append(row_dict)

    return rows

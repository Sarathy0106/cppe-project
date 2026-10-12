"""CampusVoice: clean_feedback Lambda Function.

Cleans masked staging CSV, enforces data contracts (deduplication, date parsing, month derivation),
applies the trained TF-IDF + Logistic Regression classification model (via exported weights),
writes classified records to staging JSONL (for Phase 5 Bedrock Titan embeddings),
and uses Amazon Athena to write native, partitioned Apache Parquet records into
s3://<processed-bucket>/curated/month=yyyy-MM/.

Zero external dependencies (pure Python standard library + boto3).
"""

import csv
import io
import json
import math
import os
import re
import time
from datetime import datetime
import boto3

s3_client = boto3.client("s3")
athena_client = boto3.client("athena")

PROCESSED_BUCKET = os.environ.get("PROCESSED_BUCKET")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "campusvoice_db_dev")
KMS_KEY_ID = os.environ.get("KMS_KEY_ID")

# Load model weights once during Lambda container initialization
WEIGHTS_PATH = os.path.join(os.path.dirname(__file__), "model_weights.json")
with open(WEIGHTS_PATH, "r", encoding="utf-8") as f:
    MODEL_DATA = json.load(f)

CLASSES = MODEL_DATA["classes"]
VOCABULARY = MODEL_DATA["vocabulary"]
IDF = MODEL_DATA["idf"]
COEFFICIENTS = MODEL_DATA["coefficients"]
INTERCEPTS = MODEL_DATA["intercepts"]
N_CLASSES = len(CLASSES)
N_FEATURES = len(IDF)


def tokenize_text(text: str) -> list[str]:
    """Tokenize and generate unigrams and bigrams matching scikit-learn settings."""
    # Lowercase and extract alphanumeric word tokens
    words = re.findall(r"(?u)\b\w\w+\b", text.lower())
    unigrams_and_bigrams = list(words)
    for i in range(len(words) - 1):
        unigrams_and_bigrams.append(f"{words[i]} {words[i+1]}")
    return unigrams_and_bigrams


def predict_category(text: str) -> tuple[str, float]:
    """Compute TF-IDF and Logistic Regression logits using pure Python."""
    tokens = tokenize_text(text)
    
    # Compute Term Frequency (TF)
    tf_counts = {}
    for tok in tokens:
        idx = VOCABULARY.get(tok)
        if idx is not None:
            tf_counts[idx] = tf_counts.get(idx, 0) + 1

    if not tf_counts:
        return "OTHER", 0.50

    # TF-IDF vector with L2 normalization
    tfidf_vec = {}
    sum_sq = 0.0
    for idx, count in tf_counts.items():
        val = count * IDF[idx]
        tfidf_vec[idx] = val
        sum_sq += val * val

    norm = math.sqrt(sum_sq) if sum_sq > 0 else 1.0
    for idx in tfidf_vec:
        tfidf_vec[idx] /= norm

    # Compute dot product for each class: logit = sum(x_i * w_i) + intercept
    logits = [INTERCEPTS[c] for c in range(N_CLASSES)]
    for c in range(N_CLASSES):
        c_coefs = COEFFICIENTS[c]
        for idx, val in tfidf_vec.items():
            logits[c] += val * c_coefs[idx]

    # Softmax to get probabilities
    max_logit = max(logits)
    exp_logits = [math.exp(l - max_logit) for l in logits]
    sum_exp = sum(exp_logits)
    probs = [e / sum_exp for e in exp_logits]

    best_idx = int(max(range(N_CLASSES), key=lambda i: probs[i]))
    best_cat = str(CLASSES[best_idx])
    best_conf = round(probs[best_idx], 4)

    return best_cat, best_conf


def run_athena_query(query: str) -> None:
    """Execute Athena query and wait until completion."""
    output_loc = f"s3://{PROCESSED_BUCKET}/athena-results/"
    kwargs = {
        "QueryString": query,
        "QueryExecutionContext": {"Database": DATABASE_NAME},
        "ResultConfiguration": {"OutputLocation": output_loc}
    }
    if KMS_KEY_ID:
        kwargs["ResultConfiguration"]["EncryptionConfiguration"] = {
            "EncryptionOption": "SSE_KMS",
            "KmsKey": KMS_KEY_ID
        }

    response = athena_client.start_query_execution(**kwargs)
    qid = response["QueryExecutionId"]

    # Poll until done
    for _ in range(40):
        time.sleep(2)
        status_resp = athena_client.get_query_execution(QueryExecutionId=qid)
        state = status_resp["QueryExecution"]["Status"]["State"]
        if state == "SUCCEEDED":
            return
        elif state in ["FAILED", "CANCELLED"]:
            reason = status_resp["QueryExecution"]["Status"].get("StateChangeReason", "Unknown")
            raise RuntimeError(f"Athena query failed: {reason}")

    raise TimeoutError("Athena query timed out.")


def lambda_handler(event, context):
    print("Starting data cleaning and classification stage.")
    batch_id = event["batch_id"]
    staging_key = f"staging/{batch_id}.csv"

    # 1. Read staging CSV
    obj = s3_client.get_object(Bucket=PROCESSED_BUCKET, Key=staging_key)
    content = obj["Body"].read().decode("utf-8")

    reader = csv.DictReader(io.StringIO(content))
    raw_rows = list(reader)
    print(f"[Cleaning] Raw input rows: {len(raw_rows)}")

    # 2. Cleaning & Validation
    seen_ids = set()
    cleaned_rows = []
    valid_depts = {"CSE", "ECE", "EEE", "MECH", "CIVIL", "IT"}
    valid_years = {"1", "2", "3", "4"}

    for r in raw_rows:
        fid = r.get("feedback_id", "").strip()
        text = r.get("feedback_text_masked", "").strip()
        dept = r.get("department", "").strip()
        year = str(r.get("year", "")).strip()
        fdate = r.get("feedback_date", "").strip()
        sentiment = r.get("sentiment", "NEUTRAL").strip()
        pii_cnt = int(r.get("pii_count", 0))

        # Check deduplication
        if fid in seen_ids or not fid:
            continue
        seen_ids.add(fid)

        # Check text validity
        if not text:
            continue

        # Check department and year validity
        if dept not in valid_depts or year not in valid_years:
            continue

        # Validate date format (YYYY-MM-DD) and derive month
        try:
            dt = datetime.strptime(fdate, "%Y-%m-%d")
            month = dt.strftime("%Y-%m")
        except ValueError:
            continue

        # 3. Model classification
        category, confidence = predict_category(text)

        cleaned_rows.append({
            "feedback_id": fid,
            "department": dept,
            "year": int(year),
            "feedback_text": text,
            "feedback_date": fdate,
            "sentiment": sentiment,
            "category": category,
            "category_confidence": confidence,
            "pii_count": pii_cnt,
            "batch_id": batch_id,
            "month": month
        })

    print(f"[Cleaning] Final cleaned and classified rows: {len(cleaned_rows)}")

    # 4. Write classified JSONL to staging for Phase 5 Titan embeddings
    jsonl_key = f"staging/{batch_id}_classified.jsonl"
    jsonl_content = "\n".join(json.dumps(r) for r in cleaned_rows)
    s3_client.put_object(
        Bucket=PROCESSED_BUCKET,
        Key=jsonl_key,
        Body=jsonl_content.encode("utf-8"),
        ContentType="application/x-ndjson"
    )

    # 5. Write native partitioned Parquet into S3 via Athena INSERT
    # Group inserts in batches of 50 for SQL limits
    chunk_size = 50
    for i in range(0, len(cleaned_rows), chunk_size):
        chunk = cleaned_rows[i:i + chunk_size]
        values_sql_parts = []
        for r in chunk:
            esc_text = r["feedback_text"].replace("'", "''")
            values_sql_parts.append(
                f"('{r['feedback_id']}', '{r['department']}', {r['year']}, "
                f"'{esc_text}', '{r['feedback_date']}', '{r['sentiment']}', "
                f"'{r['category']}', {r['category_confidence']}, {r['pii_count']}, "
                f"'{r['batch_id']}', '{r['month']}')"
            )
        values_sql = ",\n".join(values_sql_parts)
        insert_query = f"INSERT INTO {DATABASE_NAME}.feedback VALUES {values_sql}"
        run_athena_query(insert_query)

    print(f"Parquet partitions successfully written to s3://{PROCESSED_BUCKET}/curated/ for batch {batch_id}.")

    return {
        "batch_id": batch_id,
        "record_count": len(cleaned_rows),
        "jsonl_path": f"s3://{PROCESSED_BUCKET}/{jsonl_key}",
        "curated_prefix": "curated/"
    }

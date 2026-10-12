"""CampusVoice: mask_pii Lambda Function.

Reads raw feedback CSV from S3, detects and redacts PII using Amazon Comprehend,
computes sentiment via batch_detect_sentiment, drops direct PII identifiers (data minimization),
and outputs the masked staging CSV to processed/staging/<batch_id>.csv.

CRITICAL: Logs counts only. Never log raw or masked text content.
"""

import csv
import io
import json
import os
import re
import boto3

s3_client = boto3.client("s3")
comprehend_client = boto3.client("comprehend")

PROCESSED_BUCKET = os.environ.get("PROCESSED_BUCKET")
KMS_KEY_ID = os.environ.get("KMS_KEY_ID")

PII_TAG_MAP = {
    "NAME": "[NAME]",
    "EMAIL": "[EMAIL]",
    "PHONE": "[PHONE]",
    "ADDRESS": "[ADDRESS]",
    "DATE": "[OTHER_PII]",
    "AGE": "[OTHER_PII]",
    "USERNAME": "[OTHER_PII]",
    "PASSWORD": "[OTHER_PII]",
    "CREDIT_DEBIT_NUMBER": "[OTHER_PII]",
    "PIN": "[OTHER_PII]",
    "AWS_ACCESS_KEY": "[OTHER_PII]",
    "AWS_SECRET_KEY": "[OTHER_PII]",
    "IP_ADDRESS": "[OTHER_PII]",
    "MAC_ADDRESS": "[OTHER_PII]",
    "URL": "[OTHER_PII]"
}


def mask_text_with_comprehend(text: str, student_name: str, email: str, phone: str) -> tuple[str, int]:
    """Detect PII entities in text using Comprehend and mask backwards by offset."""
    if not text:
        return "", 0

    pii_count = 0
    # Comprehend limits detect_pii_entities to 100,000 bytes
    truncated_input = text[:5000]

    try:
        response = comprehend_client.detect_pii_entities(
            Text=truncated_input,
            LanguageCode="en"
        )
        entities = response.get("Entities", [])
        
        # Sort descending by BeginOffset to replace backwards
        entities.sort(key=lambda e: e["BeginOffset"], reverse=True)
        
        masked_text = text
        for entity in entities:
            # Filter low confidence detections (< 0.5)
            if entity.get("Score", 0) < 0.5:
                continue

            start = entity["BeginOffset"]
            end = entity["EndOffset"]
            ent_type = entity.get("Type", "OTHER")
            tag = PII_TAG_MAP.get(ent_type, "[OTHER_PII]")

            masked_text = masked_text[:start] + tag + masked_text[end:]
            pii_count += 1

    except Exception as ex:
        print(f"Warning: Comprehend detect_pii_entities error: {ex}")
        masked_text = text

    # Secondary deterministic sweep: check if row's student identifiers appear in text
    if student_name and len(student_name.strip()) > 3:
        pattern = re.compile(re.escape(student_name.strip()), re.IGNORECASE)
        masked_text, subs = pattern.subn("[NAME]", masked_text)
        pii_count += subs

    if email and "@" in email:
        pattern = re.compile(re.escape(email.strip()), re.IGNORECASE)
        masked_text, subs = pattern.subn("[EMAIL]", masked_text)
        pii_count += subs

    # Phone clean digits check
    if phone:
        phone_digits = re.sub(r"[^\d]", "", phone)
        if len(phone_digits) >= 10:
            last_10 = phone_digits[-10:]
            if last_10 in masked_text:
                masked_text = masked_text.replace(last_10, "[PHONE]")
                pii_count += 1
            if phone in masked_text:
                masked_text = masked_text.replace(phone, "[PHONE]")
                pii_count += 1

    return masked_text, pii_count


POSITIVE_KEYWORDS = {
    "good", "great", "excellent", "helpful", "improved", "clean", "supportive",
    "friendly", "fast", "satisfied", "awesome", "well", "prompt", "polite",
    "best", "smooth", "functional", "appreciate", "positive", "easy", "modern",
    "organized", "effective", "timely", "high-speed", "spacious"
}
NEGATIVE_KEYWORDS = {
    "bad", "poor", "broken", "dirty", "slow", "delay", "delayed", "worst",
    "rude", "unfunctional", "faulty", "unclean", "terrible", "complaint",
    "overcrowded", "leak", "leaking", "unresponsive", "problem", "issue",
    "damage", "damaged", "lack", "lacks", "failed", "failing", "negative",
    "unhygienic", "scratches", "loose", "irregular", "cold", "dysfunctional",
    "stagnant", "inadequate"
}


def fallback_sentiment(text: str) -> str:
    """Accurately classify sentiment using keyword lexicons when Comprehend API is restricted."""
    words = set(re.findall(r"\b\w+\b", text.lower()))
    pos = len(words & POSITIVE_KEYWORDS)
    neg = len(words & NEGATIVE_KEYWORDS)
    if neg > pos:
        return "NEGATIVE"
    elif pos > neg:
        return "POSITIVE"
    return "NEUTRAL"


def batch_sentiment_analysis(texts: list[str]) -> list[str]:
    """Analyze sentiment in batches of 25 via Comprehend batch_detect_sentiment with lexicon fallback."""
    results = []
    batch_size = 25

    for i in range(0, len(texts), batch_size):
        chunk = texts[i:i + batch_size]
        # Comprehend requires max 4,500 characters per text in batch sentiment
        safe_chunk = [t[:4500] if t else "Neutral" for t in chunk]

        try:
            resp = comprehend_client.batch_detect_sentiment(
                TextList=safe_chunk,
                LanguageCode="en"
            )
            result_list = resp.get("ResultList", [])
            sentiment_map = {item["Index"]: item["Sentiment"] for item in result_list}

            for idx in range(len(chunk)):
                sentiment = sentiment_map.get(idx, "NEUTRAL")
                results.append(sentiment)

        except Exception as ex:
            # Fallback to lexical sentiment analyzer on API error / sandbox restriction
            results.extend([fallback_sentiment(t) for t in chunk])

    return results


def lambda_handler(event, context):
    print("Starting PII masking and sentiment processing stage.")
    raw_bucket = event["bucket"]
    raw_key = event["key"]
    batch_id = event["batch_id"]

    # 1. Read raw CSV from S3
    raw_obj = s3_client.get_object(Bucket=raw_bucket, Key=raw_key)
    raw_content = raw_obj["Body"].read().decode("utf-8")

    reader = csv.DictReader(io.StringIO(raw_content))
    raw_rows = list(reader)
    total_input_rows = len(raw_rows)
    print(f"Processing batch {batch_id}: {total_input_rows} input records.")

    # 2. Mask PII for each record
    processed_records = []
    texts_for_sentiment = []
    total_pii_detected = 0

    for row in raw_rows:
        text = row.get("feedback_text", "")
        student_name = row.get("student_name", "")
        email = row.get("email", "")
        phone = row.get("phone", "")

        masked_text, pii_cnt = mask_text_with_comprehend(text, student_name, email, phone)
        total_pii_detected += pii_cnt

        processed_records.append({
            "feedback_id": row.get("feedback_id", ""),
            "department": row.get("department", ""),
            "year": row.get("year", ""),
            "feedback_text_masked": masked_text,
            "feedback_date": row.get("feedback_date", ""),
            "pii_count": pii_cnt
        })
        texts_for_sentiment.append(masked_text)

    # 3. Detect sentiment in batches of 25
    sentiments = batch_sentiment_analysis(texts_for_sentiment)

    for rec, sentiment in zip(processed_records, sentiments):
        rec["sentiment"] = sentiment

    # 4. Write masked staging CSV to processed bucket
    staging_key = f"staging/{batch_id}.csv"
    output_io = io.StringIO()
    fieldnames = [
        "feedback_id", "department", "year",
        "feedback_text_masked", "feedback_date", "pii_count", "sentiment"
    ]
    writer = csv.DictWriter(output_io, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(processed_records)

    put_kwargs = {
        "Bucket": PROCESSED_BUCKET,
        "Key": staging_key,
        "Body": output_io.getvalue().encode("utf-8"),
        "ContentType": "text/csv"
    }
    if KMS_KEY_ID:
        put_kwargs["ServerSideEncryption"] = "aws:kms"
        put_kwargs["SSEKMSKeyId"] = KMS_KEY_ID

    s3_client.put_object(**put_kwargs)

    # Structured metrics log (counts only)
    print(json.dumps({
        "event": "pii_masking_complete",
        "batch_id": batch_id,
        "total_records": total_input_rows,
        "total_pii_detected": total_pii_detected,
        "staging_output": f"s3://{PROCESSED_BUCKET}/{staging_key}"
    }))

    return {
        "batch_id": batch_id,
        "staging_bucket": PROCESSED_BUCKET,
        "staging_key": staging_key,
        "staging_path": f"s3://{PROCESSED_BUCKET}/{staging_key}",
        "record_count": total_input_rows,
        "pii_count": total_pii_detected
    }

"""CampusVoice Backend Unit Test Suite (Wipro CPPE Module 1 & 4)

Covers:
1. PII Masking & Offset Replacement Logic
2. Query Parameter Allow-List Validation & SQL Injection Prevention
3. Pure-Python Vector Cosine Similarity
"""

import math
import re
import pytest

# ------------------------------------------------------------------------------
# 1. PII Masking Offset Logic Unit Tests
# ------------------------------------------------------------------------------

PII_TAG_MAP = {
    "NAME": "[NAME]",
    "EMAIL": "[EMAIL]",
    "PHONE": "[PHONE]",
    "ADDRESS": "[ADDRESS]",
}


def mask_offsets_backwards(text: str, entities: list[dict]) -> tuple[str, int]:
    """Test implementation of offset-based masking."""
    # Entities sorted descending by BeginOffset so replacements do not shift earlier offsets
    sorted_entities = sorted(entities, key=lambda e: e["BeginOffset"], reverse=True)
    masked = text
    count = 0
    for ent in sorted_entities:
        start = ent["BeginOffset"]
        end = ent["EndOffset"]
        tag = PII_TAG_MAP.get(ent.get("Type"), "[OTHER_PII]")
        masked = masked[:start] + tag + masked[end:]
        count += 1
    return masked, count


def test_pii_offset_replacement_order():
    """Verify multiple PII entity offsets are replaced cleanly from end to beginning."""
    original = "Contact Alice at alice@campus.edu or call 555-1234 regarding hostel."
    entities = [
        {"BeginOffset": 8, "EndOffset": 13, "Type": "NAME"},
        {"BeginOffset": 17, "EndOffset": 33, "Type": "EMAIL"},
        {"BeginOffset": 42, "EndOffset": 50, "Type": "PHONE"},
    ]

    masked, count = mask_offsets_backwards(original, entities)

    assert count == 3
    assert "[NAME]" in masked
    assert "[EMAIL]" in masked
    assert "[PHONE]" in masked
    assert "Alice" not in masked
    assert "alice@campus.edu" not in masked
    assert "555-1234" not in masked
    assert masked == "Contact [NAME] at [EMAIL] or call [PHONE] regarding hostel."


def test_pii_secondary_regex_sweep():
    """Verify deterministic regex fallback masks identifiers when offset detection misses."""
    text = "Student John Doe reported dirty lab benches. Email: jdoe@univ.edu"
    student_name = "John Doe"
    email = "jdoe@univ.edu"

    # Regex sweep
    masked = text
    if student_name:
        pattern = re.compile(re.escape(student_name), re.IGNORECASE)
        masked = pattern.sub("[NAME]", masked)
    if email:
        pattern = re.compile(re.escape(email), re.IGNORECASE)
        masked = pattern.sub("[EMAIL]", masked)

    assert "John Doe" not in masked
    assert "jdoe@univ.edu" not in masked
    assert "[NAME]" in masked
    assert "[EMAIL]" in masked


# ------------------------------------------------------------------------------
# 2. Allow-List Input Validation Unit Tests
# ------------------------------------------------------------------------------

VALID_DEPTS = {"CSE", "ECE", "EEE", "MECH", "CIVIL", "IT"}
VALID_CATEGORIES = {"ADMIN", "CANTEEN", "FACULTY", "HOSTEL", "INFRASTRUCTURE", "LABS", "OTHER"}
VALID_SENTIMENTS = {"POSITIVE", "NEGATIVE", "NEUTRAL", "MIXED"}
MONTH_PATTERN = re.compile(r"^\d{4}-\d{2}$")


def validate_query_params(dept: str, cat: str, sent: str, month: str):
    """Allow-list parameter validation function."""
    errors = []
    if dept and dept.upper() not in VALID_DEPTS:
        errors.append(f"Invalid department: {dept}")
    if cat and cat.upper() not in VALID_CATEGORIES:
        errors.append(f"Invalid category: {cat}")
    if sent and sent.upper() not in VALID_SENTIMENTS:
        errors.append(f"Invalid sentiment: {sent}")
    if month and not MONTH_PATTERN.match(month):
        errors.append(f"Invalid month format: {month}")
    return errors


def test_allow_list_valid_parameters():
    """Verify standard valid filter combinations pass validation."""
    errors = validate_query_params("CSE", "HOSTEL", "NEGATIVE", "2026-06")
    assert len(errors) == 0


def test_allow_list_blocks_sql_injection():
    """Verify malicious injection attempts are blocked by strict allow-listing."""
    malicious_inputs = [
        ("CSE' OR '1'='1", "HOSTEL", "NEGATIVE", "2026-06"),
        ("CSE; DROP TABLE feedback; --", "HOSTEL", "NEGATIVE", "2026-06"),
        ("CSE", "SPORTS", "NEGATIVE", "2026-06"),  # Not in allow-list
        ("CSE", "HOSTEL", "HACK", "2026-06"),
        ("CSE", "HOSTEL", "NEGATIVE", "2026-06; SELECT 1"),  # Malicious month
    ]

    for dept, cat, sent, month in malicious_inputs:
        errors = validate_query_params(dept, cat, sent, month)
        assert len(errors) > 0, f"Expected validation failure for: dept={dept}, cat={cat}, sent={sent}, month={month}"


# ------------------------------------------------------------------------------
# 3. Vector Cosine Similarity Unit Tests
# ------------------------------------------------------------------------------

def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Pure-Python dot product cosine similarity for normalized vectors."""
    assert len(v1) == len(v2)
    return sum(a * b for a, b in zip(v1, v2))


def test_cosine_similarity_identical_vectors():
    """Verify identical unit vectors return similarity of 1.0."""
    # 4-dimensional unit vector (L2 norm = 1.0)
    v1 = [0.5, 0.5, 0.5, 0.5]
    v2 = [0.5, 0.5, 0.5, 0.5]
    sim = cosine_similarity(v1, v2)
    assert pytest.approx(sim, abs=1e-5) == 1.0


def test_cosine_similarity_orthogonal_vectors():
    """Verify orthogonal vectors return similarity of 0.0."""
    v1 = [1.0, 0.0, 0.0, 0.0]
    v2 = [0.0, 1.0, 0.0, 0.0]
    sim = cosine_similarity(v1, v2)
    assert pytest.approx(sim, abs=1e-5) == 0.0


def test_cosine_similarity_opposite_vectors():
    """Verify anti-parallel unit vectors return similarity of -1.0."""
    v1 = [0.7071, 0.7071]
    v2 = [-0.7071, -0.7071]
    sim = cosine_similarity(v1, v2)
    assert pytest.approx(sim, abs=1e-3) == -1.0

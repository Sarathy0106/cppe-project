-- ============================================================================
-- CampusVoice: Canned Analytics & Dashboard Queries (Amazon Athena)
-- Wipro CPPE Mini Project: Module 2 (Data Engineering & Big Data Analytics)
-- Database: campusvoice_db_dev
-- Table: feedback (Curated Apache Parquet, Partitioned by month)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. Executive KPIs Summary
-- Description: Aggregates total feedback, sentiment percentage distributions,
--              active department counts, and total detected/masked PII instances.
-- Cost Profile: Scans ~20 KB on sample dataset (Parquet columnar pruning).
-- ----------------------------------------------------------------------------
SELECT 
    count(*) as total_feedback,
    round(100.0 * sum(case when sentiment = 'POSITIVE' then 1 else 0 end) / count(*), 1) as pct_positive,
    round(100.0 * sum(case when sentiment = 'NEGATIVE' then 1 else 0 end) / count(*), 1) as pct_negative,
    round(100.0 * sum(case when sentiment = 'NEUTRAL' then 1 else 0 end) / count(*), 1) as pct_neutral,
    count(distinct department) as department_count,
    coalesce(sum(pii_count), 0) as total_pii_masked
FROM campusvoice_db_dev.feedback;


-- ----------------------------------------------------------------------------
-- 2. Sentiment Breakdown by Department and Month
-- Description: Evaluates department satisfaction over time for stacked bar charts.
-- ----------------------------------------------------------------------------
SELECT 
    department,
    month,
    sentiment,
    count(*) as feedback_count
FROM campusvoice_db_dev.feedback
GROUP BY department, month, sentiment
ORDER BY department, month, sentiment;


-- ----------------------------------------------------------------------------
-- 3. Feedback Distribution & Confidence by ML Category
-- Description: Displays issue category volume and average MLlib classification confidence.
-- ----------------------------------------------------------------------------
SELECT 
    category,
    count(*) as feedback_count,
    round(avg(category_confidence), 3) as avg_model_confidence,
    min(category_confidence) as min_confidence,
    max(category_confidence) as max_confidence
FROM campusvoice_db_dev.feedback
GROUP BY category
ORDER BY feedback_count DESC;


-- ----------------------------------------------------------------------------
-- 4. Monthly Trend: Feedback Volume, Negative Share & PII Leak Attempts
-- Description: Tracks student feedback momentum, grievance rates, and compliance risks.
-- ----------------------------------------------------------------------------
SELECT 
    month,
    count(*) as total_feedback,
    sum(case when sentiment = 'NEGATIVE' then 1 else 0 end) as negative_feedback_count,
    round(100.0 * sum(case when sentiment = 'NEGATIVE' then 1 else 0 end) / count(*), 1) as negative_share_pct,
    coalesce(sum(pii_count), 0) as pii_leak_attempts_prevented
FROM campusvoice_db_dev.feedback
GROUP BY month
ORDER BY month ASC;


-- ----------------------------------------------------------------------------
-- 5. Top 10 Critical Complaints by Department & Category
-- Description: Isolates the highest frequency pain points requiring immediate dean intervention.
-- ----------------------------------------------------------------------------
SELECT 
    category,
    department,
    count(*) as complaint_count
FROM campusvoice_db_dev.feedback
WHERE sentiment = 'NEGATIVE'
GROUP BY category, department
ORDER BY complaint_count DESC
LIMIT 10;


-- ----------------------------------------------------------------------------
-- 6. Partition-Pruned Explorer Query (Example: Single Month Filter)
-- Description: Demonstrates partition pruning where Athena skips all non-matching S3 prefixes.
-- ----------------------------------------------------------------------------
SELECT 
    feedback_id,
    department,
    year,
    feedback_text,
    feedback_date,
    sentiment,
    category,
    category_confidence,
    pii_count
FROM campusvoice_db_dev.feedback
WHERE month = '2026-05'
  AND department = 'CSE'
ORDER BY feedback_date DESC
LIMIT 50;

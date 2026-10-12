-- ==============================================================================
-- CampusVoice: Redshift Serverless Dimensional Modeling (Wipro CPPE Module 2)
-- Star Schema: fact_feedback, dim_department, dim_category, dim_date
-- ==============================================================================

-- 1. Create Analytics Schema
CREATE SCHEMA IF NOT EXISTS campusvoice_dw;
SET search_path TO campusvoice_dw, public;

-- ------------------------------------------------------------------------------
-- 2. Dimension Tables
-- ------------------------------------------------------------------------------

-- Department Dimension
CREATE TABLE IF NOT EXISTS dim_department (
    dept_key INT IDENTITY(1,1),
    dept_code VARCHAR(10) NOT NULL UNIQUE,
    dept_name VARCHAR(100) NOT NULL,
    division VARCHAR(50) DEFAULT 'Engineering',
    PRIMARY KEY (dept_key)
) DISTSTYLE ALL;

-- Category Dimension
CREATE TABLE IF NOT EXISTS dim_category (
    category_key INT IDENTITY(1,1),
    category_name VARCHAR(50) NOT NULL UNIQUE,
    category_group VARCHAR(50) NOT NULL,
    PRIMARY KEY (category_key)
) DISTSTYLE ALL;

-- Date Dimension
CREATE TABLE IF NOT EXISTS dim_date (
    date_key INT NOT NULL,
    full_date DATE NOT NULL UNIQUE,
    month_id VARCHAR(7) NOT NULL,
    year_num INT NOT NULL,
    quarter_num INT NOT NULL,
    semester_id VARCHAR(20) NOT NULL,
    PRIMARY KEY (date_key)
) DISTSTYLE ALL;

-- ------------------------------------------------------------------------------
-- 3. Fact Table
-- ------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS fact_feedback (
    feedback_key BIGINT IDENTITY(1,1),
    feedback_id VARCHAR(50) NOT NULL,
    dept_key INT NOT NULL REFERENCES dim_department(dept_key),
    category_key INT NOT NULL REFERENCES dim_category(category_key),
    date_key INT NOT NULL REFERENCES dim_date(date_key),
    sentiment VARCHAR(20) NOT NULL,
    sentiment_score NUMERIC(5,4) NOT NULL,
    is_positive INT NOT NULL,
    is_negative INT NOT NULL,
    is_neutral INT NOT NULL,
    has_pii INT DEFAULT 0,
    text_character_length INT NOT NULL,
    PRIMARY KEY (feedback_key)
)
DISTKEY(dept_key)
COMPOUND SORTKEY(date_key, category_key);

-- ------------------------------------------------------------------------------
-- 4. Initial Dimension Seeding
-- ------------------------------------------------------------------------------

INSERT INTO dim_department (dept_code, dept_name, division) VALUES
('CSE', 'Computer Science and Engineering', 'Computing & Informatics'),
('ECE', 'Electronics and Communication Engineering', 'Electrical Sciences'),
('MECH', 'Mechanical Engineering', 'Mechanical Sciences'),
('CIVIL', 'Civil Engineering', 'Infrastructure Sciences'),
('IT', 'Information Technology', 'Computing & Informatics'),
('AI_DS', 'Artificial Intelligence & Data Science', 'Computing & Informatics'),
('MBA', 'Master of Business Administration', 'Management Studies');

INSERT INTO dim_category (category_name, category_group) VALUES
('FACULTY', 'Academic Quality'),
('HOSTEL', 'Campus Living'),
('CANTEEN', 'Student Welfare'),
('INFRASTRUCTURE', 'Facilities & Campus'),
('EXAMS', 'Academics & Evaluation'),
('LIBRARY', 'Learning Resources'),
('LABS', 'Practical Training'),
('GENERAL', 'Institutional Services');

-- ------------------------------------------------------------------------------
-- 5. COPY Command from Curated Parquet Data Lake
-- ------------------------------------------------------------------------------

/*
COPY campusvoice_dw.staging_feedback
FROM 's3://campusvoice-processed-657878533694-dev/curated/'
IAM_ROLE 'arn:aws:iam::657878533694:role/campusvoice-redshift-role'
FORMAT AS PARQUET;
*/

-- ------------------------------------------------------------------------------
-- 6. Analytical Star Schema Queries
-- ------------------------------------------------------------------------------

-- Query 1: Negative Sentiment Complaint Density by Department & Category Group
SELECT
    d.dept_code,
    c.category_group,
    COUNT(f.feedback_key) AS total_feedback_count,
    SUM(f.is_negative) AS negative_complaint_count,
    ROUND(SUM(f.is_negative)::NUMERIC / COUNT(f.feedback_key) * 100, 2) AS complaint_percentage
FROM fact_feedback f
JOIN dim_department d ON f.dept_key = d.dept_key
JOIN dim_category c ON f.category_key = c.category_key
GROUP BY d.dept_code, c.category_group
ORDER BY negative_complaint_count DESC;

-- Query 2: Multi-Semester Sentiment Evolution (Academic Cohort Analysis)
SELECT
    dt.semester_id,
    dt.month_id,
    COUNT(f.feedback_key) AS total_responses,
    ROUND(AVG(f.sentiment_score), 4) AS avg_confidence,
    ROUND(SUM(f.is_positive)::NUMERIC / COUNT(f.feedback_key) * 100, 2) AS positive_share,
    ROUND(SUM(f.is_negative)::NUMERIC / COUNT(f.feedback_key) * 100, 2) AS negative_share
FROM fact_feedback f
JOIN dim_date dt ON f.date_key = dt.date_key
GROUP BY dt.semester_id, dt.month_id
ORDER BY dt.month_id ASC;

-- Query 3: Top Facilities Needing Immediate Administrative Action
SELECT
    c.category_name,
    COUNT(f.feedback_key) AS issue_volume,
    ROUND(AVG(f.sentiment_score), 3) AS model_confidence,
    RANK() OVER (ORDER BY COUNT(f.feedback_key) DESC) AS priority_rank
FROM fact_feedback f
JOIN dim_category c ON f.category_key = c.category_key
WHERE f.is_negative = 1
GROUP BY c.category_name
LIMIT 5;

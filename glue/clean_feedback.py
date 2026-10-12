"""CampusVoice: clean_feedback PySpark Job (Glue 4.0).

Cleans masked staging CSV, enforces data contracts, validates departments/years/dates,
derives partitioning month, applies fitted PipelineModel to infer category and confidence,
and writes curated Parquet partitioned by month to S3 (mode=append).
Also writes a staging JSONL for efficient embedding generation in Phase 5.
"""

import sys
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.ml import PipelineModel
from pyspark.sql.functions import col, trim, udf, to_date, date_format
from pyspark.sql.types import DoubleType, StringType, IntegerType

# Initialize Glue / Spark Context
args = getResolvedOptions(sys.argv, [
    "JOB_NAME",
    "batch_id",
    "input",
    "output",
    "model_path",
    "jsonl_output"
])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

batch_id = args["batch_id"]
input_path = args["input"]
output_path = args["output"]
model_path = args["model_path"]
jsonl_output_path = args.get("jsonl_output")

print(f"Starting feedback cleaning for batch: {batch_id}")
print(f"Input staging file: {input_path}")
print(f"Curated Parquet destination: {output_path}")

# 1. Read staging CSV
raw_df = spark.read.option("header", "true").csv(input_path)
initial_count = raw_df.count()
print(f"[Cleaning] Rows in: {initial_count}")

# 2. Drop duplicate feedback_id
dedup_df = raw_df.dropDuplicates(["feedback_id"])
duplicates_removed = initial_count - dedup_df.count()
print(f"[Cleaning] Duplicates removed: {duplicates_removed}")

# 3. Drop null or empty text and trim whitespace
valid_text_df = dedup_df.filter(
    col("feedback_text_masked").isNotNull() & (trim(col("feedback_text_masked")) != "")
).withColumn("feedback_text", trim(col("feedback_text_masked")))
nulls_removed = dedup_df.count() - valid_text_df.count()
print(f"[Cleaning] Nulls / empty texts removed: {nulls_removed}")

# 4. Validate department and year
valid_depts = ["CSE", "ECE", "EEE", "MECH", "CIVIL", "IT"]
valid_years = ["1", "2", "3", "4", 1, 2, 3, 4]

contract_df = valid_text_df.filter(
    col("department").isin(valid_depts) & col("year").isin(valid_years)
).withColumn("year", col("year").cast(IntegerType()))

# 5. Parse dates and derive month partition (yyyy-MM)
parsed_dates_df = contract_df.withColumn("parsed_date", to_date(col("feedback_date"), "yyyy-MM-dd"))
valid_dates_df = parsed_dates_df.filter(col("parsed_date").isNotNull())
invalid_dates = parsed_dates_df.count() - valid_dates_df.count()
print(f"[Cleaning] Invalid dates dropped: {invalid_dates}")

final_clean_df = valid_dates_df.withColumn(
    "month", date_format(col("parsed_date"), "yyyy-MM")
).withColumn(
    "pii_count", col("pii_count").cast(IntegerType())
)

# 6. Load fitted PipelineModel and infer categories
print(f"Loading trained Spark MLlib model from: {model_path}")
model = PipelineModel.load(model_path)

# Extract label list from the StringIndexerModel stage
labels = None
for stage in model.stages:
    if hasattr(stage, "labels"):
        labels = stage.labels
        break

if not labels:
    labels = ["HOSTEL", "FACULTY", "LABS", "CANTEEN", "INFRASTRUCTURE", "ADMIN", "OTHER"]

print(f"Model category labels: {labels}")

# UDF to extract max probability from vector
@udf(returnType=DoubleType())
def extract_confidence(prob_vec):
    if prob_vec is not None:
        try:
            return round(float(max(prob_vec.toArray())), 4)
        except Exception:
            return 1.0
    return 1.0

# UDF to map numeric prediction to label string
@udf(returnType=StringType())
def map_prediction_to_category(pred_idx):
    if pred_idx is not None:
        try:
            idx = int(pred_idx)
            if 0 <= idx < len(labels):
                return labels[idx]
        except Exception:
            pass
    return "OTHER"

# Predict category on clean dataset
predicted_df = model.transform(final_clean_df)

curated_df = predicted_df.withColumn(
    "category", map_prediction_to_category(col("prediction"))
).withColumn(
    "category_confidence", extract_confidence(col("probability"))
).withColumn(
    "batch_id", col("batch_id") if "batch_id" in predicted_df.columns else udf(lambda: batch_id, StringType())()
)

# Final columns per curated Parquet data contract:
# feedback_id, department, year, feedback_text, feedback_date, sentiment, category, category_confidence, pii_count, batch_id, month
selected_curated_df = curated_df.select(
    "feedback_id",
    "department",
    "year",
    "feedback_text",
    "feedback_date",
    "sentiment",
    "category",
    "category_confidence",
    "pii_count",
    "batch_id",
    "month"
)

final_rows = selected_curated_df.count()
print(f"[Cleaning Summary] Rows out: {final_rows}")

# 7. Write Parquet partitioned by month (mode=append)
print(f"Writing curated Parquet partitioned by month to: {output_path}")
selected_curated_df.write.partitionBy("month").mode("append").parquet(output_path)

# 8. Write JSONL file for embedding generation (Phase 5)
if jsonl_output_path:
    print(f"Writing classified staging JSONL to: {jsonl_output_path}")
    selected_curated_df.write.mode("overwrite").json(jsonl_output_path)

print(f"Cleaning and classification complete for batch {batch_id}.")
job.commit()

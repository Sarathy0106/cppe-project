"""CampusVoice: train_model PySpark Job (Glue 4.0).

Reads train_labeled.csv from S3, builds a text classification Spark ML Pipeline
(Tokenizer -> StopWordsRemover -> HashingTF -> IDF -> StringIndexer -> LogisticRegression).
Performs an 80/20 train/test split.
Evaluates accuracy, weighted precision, weighted recall, and F1 score.
Trains a second comparison model (NaiveBayes) to fulfill the algorithm comparison requirement.
Saves comparison metrics to models/metrics.json and the fitted PipelineModel to models/category_model/.
"""

import json
import sys
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.ml import Pipeline
from pyspark.ml.feature import Tokenizer, StopWordsRemover, HashingTF, IDF, StringIndexer
from pyspark.ml.classification import LogisticRegression, NaiveBayes
from pyspark.ml.evaluation import MulticlassClassificationEvaluator

# Initialize Glue / Spark Context
args = getResolvedOptions(sys.argv, [
    "JOB_NAME",
    "train_data_path",
    "model_output_path",
    "metrics_output_path"
])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

train_data_path = args["train_data_path"]
model_output_path = args["model_output_path"]
metrics_output_path = args["metrics_output_path"]

print(f"Loading training dataset from: {train_data_path}")
df = spark.read.option("header", "true").option("inferSchema", "true").csv(train_data_path)

# Filter nulls or empty texts
df_clean = df.filter(df["feedback_text"].isNotNull() & df["category"].isNotNull())
print(f"Total training samples: {df_clean.count()}")

# 80/20 train/test split with deterministic seed
train_df, test_df = df_clean.randomSplit([0.8, 0.2], seed=42)

# Define feature extraction pipeline
tokenizer = Tokenizer(inputCol="feedback_text", outputCol="words")
stopwords_remover = StopWordsRemover(inputCol="words", outputCol="filtered_words")
hashing_tf = HashingTF(inputCol="filtered_words", outputCol="raw_features", numFeatures=2000)
idf = IDF(inputCol="raw_features", outputCol="features")
label_indexer = StringIndexer(inputCol="category", outputCol="label").fit(train_df)

# Labels list for index mapping
label_list = label_indexer.labels
print(f"Indexed categories ({len(label_list)}): {label_list}")

# Model 1: Logistic Regression
lr = LogisticRegression(featuresCol="features", labelCol="label", maxIter=20, regParam=0.01)
lr_pipeline = Pipeline(stages=[tokenizer, stopwords_remover, hashing_tf, idf, label_indexer, lr])
lr_model = lr_pipeline.fit(train_df)
lr_predictions = lr_model.transform(test_df)

# Model 2: Naive Bayes (comparison algorithm)
nb = NaiveBayes(featuresCol="features", labelCol="label", smoothing=1.0)
nb_pipeline = Pipeline(stages=[tokenizer, stopwords_remover, hashing_tf, idf, label_indexer, nb])
nb_model = nb_pipeline.fit(train_df)
nb_predictions = nb_model.transform(test_df)

# Evaluators
evaluator_acc = MulticlassClassificationEvaluator(metricName="accuracy")
evaluator_prec = MulticlassClassificationEvaluator(metricName="weightedPrecision")
evaluator_rec = MulticlassClassificationEvaluator(metricName="weightedRecall")
evaluator_f1 = MulticlassClassificationEvaluator(metricName="f1")

# Compute metrics for Model 1 (Logistic Regression)
lr_metrics = {
    "accuracy": round(float(evaluator_acc.evaluate(lr_predictions)), 4),
    "precision": round(float(evaluator_prec.evaluate(lr_predictions)), 4),
    "recall": round(float(evaluator_rec.evaluate(lr_predictions)), 4),
    "f1_score": round(float(evaluator_f1.evaluate(lr_predictions)), 4)
}

# Compute metrics for Model 2 (Naive Bayes)
nb_metrics = {
    "accuracy": round(float(evaluator_acc.evaluate(nb_predictions)), 4),
    "precision": round(float(evaluator_prec.evaluate(nb_predictions)), 4),
    "recall": round(float(evaluator_rec.evaluate(nb_predictions)), 4),
    "f1_score": round(float(evaluator_f1.evaluate(nb_predictions)), 4)
}

print(f"Logistic Regression Evaluation: {lr_metrics}")
print(f"Naive Bayes Evaluation: {nb_metrics}")

# Prepare metrics JSON
metrics_report = {
    "evaluation_summary": {
        "primary_model": "Logistic Regression (TF-IDF)",
        "comparison_model": "Multinomial Naive Bayes (TF-IDF)",
        "train_samples": train_df.count(),
        "test_samples": test_df.count(),
        "categories": label_list
    },
    "model_comparison": [
        {"algorithm": "Logistic Regression", **lr_metrics},
        {"algorithm": "Naive Bayes", **nb_metrics}
    ],
    "selected_model": "Logistic Regression",
    "labels": label_list
}

# Save primary PipelineModel to S3
print(f"Saving fitted PipelineModel to: {model_output_path}")
lr_model.write().overwrite().save(model_output_path)

# Save metrics JSON directly via Spark RDD
metrics_json_str = json.dumps(metrics_report, indent=2)
metrics_rdd = sc.parallelize([metrics_json_str])
metrics_rdd.coalesce(1).saveAsTextFile(metrics_output_path)

print("Model training and evaluation successfully completed.")
job.commit()

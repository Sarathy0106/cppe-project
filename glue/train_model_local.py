"""Train classification models and generate metrics comparison report.

Implements TF-IDF + Logistic Regression and TF-IDF + Multinomial Naive Bayes,
evaluates both models on the test split, outputs metrics.json, and exports
the fitted model for serverless inference.
"""

import csv
import json
import os
import pickle
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    train_path = os.path.join(base_dir, "data", "train_labeled.csv")
    
    texts = []
    labels = []
    with open(train_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            txt = row.get("feedback_text", "").strip()
            cat = row.get("category", "").strip()
            if txt and cat:
                texts.append(txt)
                labels.append(cat)
                
    print(f"Loaded {len(texts)} samples from {train_path}.")
    unique_categories = sorted(list(set(labels)))
    print(f"Target categories ({len(unique_categories)}): {unique_categories}")
    
    # 80/20 train/test split with seed 42
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.20, random_state=42, stratify=labels
    )
    
    # TF-IDF Feature Extraction
    tfidf = TfidfVectorizer(max_features=2000, stop_words="english", ngram_range=(1, 2))
    X_train_vec = tfidf.fit_transform(X_train)
    X_test_vec = tfidf.transform(X_test)
    
    # Model 1: Logistic Regression
    lr = LogisticRegression(max_iter=100, C=1.0, random_state=42)
    lr.fit(X_train_vec, y_train)
    lr_preds = lr.predict(X_test_vec)
    
    # Model 2: Multinomial Naive Bayes
    nb = MultinomialNB(alpha=1.0)
    nb.fit(X_train_vec, y_train)
    nb_preds = nb.predict(X_test_vec)
    
    # Evaluation metrics
    lr_metrics = {
        "accuracy": round(float(accuracy_score(y_test, lr_preds)), 4),
        "precision": round(float(precision_score(y_test, lr_preds, average="weighted", zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, lr_preds, average="weighted", zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_test, lr_preds, average="weighted", zero_division=0)), 4)
    }
    
    nb_metrics = {
        "accuracy": round(float(accuracy_score(y_test, nb_preds)), 4),
        "precision": round(float(precision_score(y_test, nb_preds, average="weighted", zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, nb_preds, average="weighted", zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_test, nb_preds, average="weighted", zero_division=0)), 4)
    }
    
    cm = confusion_matrix(y_test, lr_preds, labels=unique_categories).tolist()
    
    print("\n--- Model Evaluation Results ---")
    print(f"Logistic Regression: {lr_metrics}")
    print(f"Naive Bayes:         {nb_metrics}")
    
    metrics_report = {
        "evaluation_summary": {
            "primary_model": "Logistic Regression (TF-IDF)",
            "comparison_model": "Multinomial Naive Bayes (TF-IDF)",
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "categories": unique_categories
        },
        "model_comparison": [
            {"algorithm": "Logistic Regression", **lr_metrics},
            {"algorithm": "Naive Bayes", **nb_metrics}
        ],
        "selected_model": "Logistic Regression",
        "confusion_matrix": {
            "labels": unique_categories,
            "matrix": cm
        }
    }
    
    # Save metrics.json
    output_dir = os.path.join(base_dir, "data", "models")
    os.makedirs(output_dir, exist_ok=True)
    metrics_file = os.path.join(output_dir, "metrics.json")
    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(metrics_report, f, indent=2)
    print(f"\nSaved metrics report to: {metrics_file}")
    
    # Export fitted model pipeline for Lambda inference
    lambda_model_dir = os.path.join(base_dir, "backend", "clean_feedback")
    os.makedirs(lambda_model_dir, exist_ok=True)
    model_export_file = os.path.join(lambda_model_dir, "category_model.pkl")
    with open(model_export_file, "wb") as f:
        pickle.dump({"vectorizer": tfidf, "model": lr, "classes": unique_categories}, f)
    print(f"Saved inference model to: {model_export_file}")

if __name__ == "__main__":
    main()

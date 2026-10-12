"""Export trained Logistic Regression model and TF-IDF vocabulary to pure JSON.
Allows Lambda to run inference with zero external C-dependencies.
"""

import json
import os
import pickle
import numpy as np

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_pkl = os.path.join(base_dir, "backend", "clean_feedback", "category_model.pkl")
    
    with open(model_pkl, "rb") as f:
        data = pickle.load(f)
        
    vec = data["vectorizer"]
    clf = data["model"]
    classes = list(clf.classes_)
    
    # Vocabulary mapping {word: feature_index}
    vocab = {k: int(v) for k, v in vec.vocabulary_.items()}
    idf = [float(x) for x in vec.idf_]
    
    # Coefficients [n_classes, n_features] and intercept [n_classes]
    coefs = [[round(float(c), 6) for c in row] for row in clf.coef_]
    intercepts = [round(float(b), 6) for b in clf.intercept_]
    
    export_data = {
        "classes": classes,
        "vocabulary": vocab,
        "idf": idf,
        "coefficients": coefs,
        "intercepts": intercepts
    }
    
    out_file = os.path.join(base_dir, "backend", "clean_feedback", "model_weights.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(export_data, f)
        
    print(f"Successfully exported model weights to: {out_file}")
    print(f"Vocabulary size: {len(vocab)}, Classes: {classes}")

if __name__ == "__main__":
    main()

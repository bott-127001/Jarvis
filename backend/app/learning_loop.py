import os
import time
from datetime import datetime
from pymongo import MongoClient
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from fastapi import FastAPI

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client["samarth"]

MODEL_PATHS = {
    'bias': 'ml_models/bias_identifier_model.pkl',
    'market_style': 'ml_models/market_style_model.pkl',
    'trap': 'ml_models/trap_detector_model.pkl',
    'reversal': 'ml_models/reversal_probability_model.pkl',
    'sr': 'ml_models/support_resistance_model.pkl',
    'entry_logic': 'ml_models/entry_logic_model.pkl',
}

MODEL_RETRAIN_LOG = "model_retrain_log"

def fetch_labeled_data(collection, feature_keys, label_key='outcome'):
    docs = list(db[collection].find({label_key: {"$exists": True}}))
    if not docs:
        return None, None
    df = pd.DataFrame(docs)
    # Flatten nested fields if needed
    for k in feature_keys:
        if '.' in k:
            parts = k.split('.')
            df[k] = df
            for p in parts:
                df[k] = df[k].apply(lambda x: x.get(p) if isinstance(x, dict) else None)
    X = df[feature_keys].values
    y = df[label_key].values
    return X, y

# --- Log retrain event ---
def log_retrain_event(module, accuracy, sample_count, feature_importances=None, error=None):
    db[MODEL_RETRAIN_LOG].insert_one({
        "module": module,
        "timestamp": datetime.utcnow(),
        "accuracy": accuracy,
        "sample_count": sample_count,
        "feature_importances": feature_importances,
        "error": error
    })

# --- Modified retrain_classifier to log events ---
def retrain_classifier(module, feature_keys):
    print(f"Retraining {module} classifier...")
    X, y = fetch_labeled_data(f"{module}_snapshots", feature_keys)
    if X is None or len(X) < 100:
        print(f"Not enough data for {module}. Skipping.")
        log_retrain_event(module, accuracy=None, sample_count=0, error="Not enough data")
        return
    clf = RandomForestClassifier(n_estimators=50, n_jobs=-1)
    clf.fit(X, y)
    joblib.dump(clf, MODEL_PATHS[module])
    # Score
    acc = clf.score(X, y)
    # Feature importances
    importances = clf.feature_importances_.tolist()
    log_retrain_event(module, accuracy=acc, sample_count=len(y), feature_importances=importances)
    print(f"Saved new model for {module} at {MODEL_PATHS[module]}")

def score_signals(module):
    docs = list(db[f"{module}_snapshots"].find({"outcome": {"$exists": True}}))
    if not docs:
        print(f"No labeled data for {module}")
        return
    df = pd.DataFrame(docs)
    acc = df['outcome'].mean()
    print(f"{module} accuracy: {acc:.2%} ({len(df)} samples)")

# --- FastAPI endpoint for manual retrain ---
app = FastAPI()

@app.post("/retrain-module")
def retrain_module(module: str):
    feature_map = {
        'bias': ['rolling_pct.call_oi', 'rolling_pct.call_iv', 'rolling_pct.call_volume',
                 'rolling_pct.put_oi', 'rolling_pct.put_iv', 'rolling_pct.put_volume'],
        'market_style': ['oi_diff', 'vol_diff', 'iv_diff', 'spot_trend_strength'],
        'trap': ['call.deception_score', 'put.deception_score'],
        'reversal': ['reversal_probability'],
        'sr': ['zones.0.confidence_score'],
        'entry_logic': ['entry_score'],
    }
    if module not in feature_map:
        return {"error": "Unknown module"}
    try:
        retrain_classifier(module, feature_map[module])
        return {"status": f"Retrained {module} successfully."}
    except Exception as e:
        log_retrain_event(module, accuracy=None, sample_count=0, error=str(e))
        return {"error": str(e)}

def learning_loop():
    # Define features for each module (adjust as needed)
    feature_map = {
        'bias': ['rolling_pct.call_oi', 'rolling_pct.call_iv', 'rolling_pct.call_volume',
                 'rolling_pct.put_oi', 'rolling_pct.put_iv', 'rolling_pct.put_volume'],
        'market_style': ['oi_diff', 'vol_diff', 'iv_diff', 'spot_trend_strength'],
        'trap': ['call.deception_score', 'put.deception_score'],
        'reversal': ['reversal_probability'],
        'sr': ['zones.0.confidence_score'],
        'entry_logic': ['entry_score'],
    }
    for module, features in feature_map.items():
        score_signals(module)
        retrain_classifier(module, features)
    print(f"Learning loop completed at {datetime.now()}")

if __name__ == "__main__":
    while True:
        learning_loop()
        time.sleep(24 * 3600)  # Run daily 
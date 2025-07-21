import os
from pymongo import MongoClient
import pandas as pd
from datetime import timedelta

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client["samarth"]

LOOKAHEAD_MINUTES = [15, 30, 45, 60]
PRICE_MOVE_THRESHOLD = 0.5  # percent

rows = []
for entry in db["entry_logic_snapshots"].find({}):
    ts = entry["timestamp"]
    user = entry["user"]
    expiry = entry["expiry"]
    direction = entry.get("entry_direction")
    # Features: module outputs, confidences, anomaly, S/R, etc.
    features = {
        "entry_score": entry.get("entry_score"),
        "confidence": entry.get("confidence"),
        "anomaly_score": entry.get("anomaly_score"),
        "bias": entry.get("raw_signals", {}).get("bias", {}).get("bias"),
        "market_style": entry.get("raw_signals", {}).get("style", {}).get("market_style"),
        "trap_call": entry.get("raw_signals", {}).get("trap", {}).get("call", {}).get("trap_detected"),
        "reversal_type": entry.get("raw_signals", {}).get("reversal", {}).get("reversal_type"),
        "sr_confidence": entry.get("raw_signals", {}).get("sr", [{}])[0].get("confidence") if entry.get("raw_signals", {}).get("sr") else None,
        # Add more as needed
    }
    spot_now = entry.get("raw_signals", {}).get("bias", {}).get("spot")
    if spot_now is None or direction not in ("long", "short"):
        continue
    entry_worked = 0
    for mins in LOOKAHEAD_MINUTES:
        future = db["option_chain_snapshots"].find_one({
            "user": user,
            "expiry": expiry,
            "timestamp": {"$gte": ts + timedelta(minutes=mins)}
        }, sort=[("timestamp", 1)])
        spot_future = future["strikes"][0].get("underlying_spot_price") if future and future.get("strikes") else None
        if spot_future is None:
            continue
        pct_move = (spot_future - spot_now) / spot_now * 100
        if direction == "long" and pct_move > PRICE_MOVE_THRESHOLD:
            entry_worked = 1
            break
        elif direction == "short" and pct_move < -PRICE_MOVE_THRESHOLD:
            entry_worked = 1
            break
    features["entry_worked"] = entry_worked
    rows.append(features)

if rows:
    df = pd.DataFrame(rows)
    df.to_csv("meta_model_training_data.csv", index=False)
    print(f"Exported {len(df)} rows to meta_model_training_data.csv")
else:
    print("No data exported.") 
import os
from pymongo import MongoClient
from datetime import timedelta
from ml_inference import predict_meta_decision

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client["samarth"]

LOOKAHEAD_MINUTES = [15, 30, 45, 60]
PRICE_MOVE_THRESHOLD = 0.5  # percent

results = []
for entry in db["entry_logic_snapshots"].find({}):
    ts = entry["timestamp"]
    user = entry["user"]
    expiry = entry["expiry"]
    direction = entry.get("entry_direction")
    # Build meta-model features
    entry_score = entry.get("entry_score")
    confidence = entry.get("confidence")
    anomaly_score = entry.get("anomaly_score")
    bias = entry.get("raw_signals", {}).get("bias", {}).get("bias")
    market_style = entry.get("raw_signals", {}).get("style", {}).get("market_style")
    trap_call = entry.get("raw_signals", {}).get("trap", {}).get("call", {}).get("trap_detected")
    reversal_type = entry.get("raw_signals", {}).get("reversal", {}).get("reversal_type")
    sr_confidence = entry.get("raw_signals", {}).get("sr", [{}])[0].get("confidence") if entry.get("raw_signals", {}).get("sr") else None
    meta_features = [entry_score, confidence, anomaly_score, bias, market_style, trap_call, reversal_type, sr_confidence]
    meta_decision = predict_meta_decision(meta_features)
    if not meta_decision["should_enter"]:
        continue
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
    results.append(entry_worked)

if results:
    win_rate = sum(results) / len(results)
    print(f"Meta-model paper trading win rate: {win_rate:.2%} over {len(results)} trades.")
else:
    print("No trades simulated.") 
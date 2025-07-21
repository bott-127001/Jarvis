import pandas as pd
from pymongo import MongoClient
from datetime import datetime, timedelta
import os
# --- CONFIG ---
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = 'samarth'
TRAP_COLL = 'trap_detector_snapshots'
CHAIN_COLL = 'option_chain_snapshots'
EXPORT_CSV = 'trap_detector_snapshots_labeled.csv'
LABEL_WINDOW_MINUTES = 10
REVERSAL_THRESHOLD = 0.15  # 0.15% move for reversal

# --- Connect to MongoDB ---
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
trap_col = db[TRAP_COLL]
chain_col = db[CHAIN_COLL]

# --- Load trap snapshots ---
trap_docs = list(trap_col.find({}))
if not trap_docs:
    print('No trap detector snapshots found!')
    exit(1)

# --- Helper: get spot price N min after timestamp ---
def get_future_spot(user, expiry, ts, minutes=10):
    future_time = ts + timedelta(minutes=minutes)
    doc = chain_col.find_one({
        'user': user,
        'expiry': expiry,
        'timestamp': {'$gte': future_time}
    }, sort=[('timestamp', 1)])
    if doc and doc.get('strikes'):
        return doc['strikes'][0].get('underlying_spot_price')
    return None

# --- Build DataFrame ---
rows = []
for doc in trap_docs:
    ts = doc.get('timestamp')
    if isinstance(ts, str):
        ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
    user = doc.get('user')
    expiry = doc.get('expiry')
    # Use call/put trap info
    for leg in ['call', 'put']:
        trap_info = doc.get(leg, {})
        trap_detected = trap_info.get('trap_detected')
        deception_score = trap_info.get('deception_score')
        trap_memory = trap_info.get('trap_memory')
        # Use spot at time of trap and after window
        spot = doc.get('spot') if 'spot' in doc else None
        future_spot = get_future_spot(user, expiry, ts, LABEL_WINDOW_MINUTES)
        if spot is None or future_spot is None:
            continue
        spot_delta = (future_spot - spot) / spot * 100
        # Label: True Trap if reversal > threshold in opposite direction
        if leg == 'call' and spot_delta < -REVERSAL_THRESHOLD:
            true_trap = 1
        elif leg == 'put' and spot_delta > REVERSAL_THRESHOLD:
            true_trap = 1
        else:
            true_trap = 0
        row = {
            'timestamp': ts,
            'user': user,
            'expiry': expiry,
            'leg': leg,
            'trap_detected': trap_detected,
            'deception_score': deception_score,
            'trap_memory': trap_memory,
            'spot_delta': spot_delta,
            'true_trap': true_trap
        }
        rows.append(row)

# --- Save to CSV ---
df = pd.DataFrame(rows)
df.to_csv(EXPORT_CSV, index=False)
print(f'Exported {len(df)} labeled rows to {EXPORT_CSV}') 
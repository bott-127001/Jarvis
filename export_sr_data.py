import pandas as pd
from pymongo import MongoClient
from datetime import datetime, timedelta
import os
# --- CONFIG ---
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = 'samarth'
SR_COLL = 'support_resistance_snapshots'
CHAIN_COLL = 'option_chain_snapshots'
EXPORT_CSV = 'support_resistance_snapshots_labeled.csv'
LABEL_WINDOW_MINUTES = 10
BOUNCE_THRESHOLD = 0.1  # 0.1% move for bounce
BREAK_THRESHOLD = 0.15  # 0.15% move for break

# --- Connect to MongoDB ---
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
sr_col = db[SR_COLL]
chain_col = db[CHAIN_COLL]

# --- Load S/R snapshots ---
sr_docs = list(sr_col.find({}))
if not sr_docs:
    print('No support/resistance snapshots found!')
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
for doc in sr_docs:
    ts = doc.get('timestamp')
    if isinstance(ts, str):
        ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
    user = doc.get('user')
    expiry = doc.get('expiry')
    zones = doc.get('zones', [])
    for zone in zones:
        zlvl = zone.get('zone_level')
        ztype = zone.get('zone_type')
        zone_state = zone.get('zone_state')
        confidence_score = zone.get('confidence_score')
        volatility_regime = zone.get('volatility_regime')
        trap_risk = zone.get('trap_risk')
        bias_suggestion = zone.get('bias_suggestion')
        signal_disagreement = zone.get('signal_disagreement')
        # Get spot at time of snapshot and after window
        spot = zlvl
        future_spot = get_future_spot(user, expiry, ts, LABEL_WINDOW_MINUTES)
        if spot is None or future_spot is None:
            continue
        spot_delta = (future_spot - spot) / spot * 100
        # Label logic
        if bias_suggestion == 'Bounce' and spot_delta < -BOUNCE_THRESHOLD:
            true_outcome = 'Bounce'
        elif bias_suggestion == 'Break' and spot_delta > BREAK_THRESHOLD:
            true_outcome = 'Break'
        elif bias_suggestion == 'Trap':
            true_outcome = 'Trap'
        else:
            true_outcome = 'Other'
        row = {
            'timestamp': ts,
            'user': user,
            'expiry': expiry,
            'zone_level': zlvl,
            'zone_type': ztype,
            'zone_state': zone_state,
            'confidence_score': confidence_score,
            'volatility_regime': volatility_regime,
            'trap_risk': trap_risk,
            'bias_suggestion': bias_suggestion,
            'signal_disagreement': signal_disagreement,
            'spot_delta': spot_delta,
            'true_outcome': true_outcome
        }
        rows.append(row)

# --- Save to CSV ---
df = pd.DataFrame(rows)
df.to_csv(EXPORT_CSV, index=False)
print(f'Exported {len(df)} labeled rows to {EXPORT_CSV}') 
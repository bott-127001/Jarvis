import pandas as pd
from pymongo import MongoClient
from datetime import datetime, timedelta
import os
# --- CONFIG ---
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = 'samarth'
ENTRY_COLL = 'entry_logic_snapshots'
CHAIN_COLL = 'option_chain_snapshots'
EXPORT_CSV = 'entry_logic_snapshots_labeled.csv'
LABEL_WINDOW_MINUTES = 10
PROFIT_THRESHOLD = 0.15  # 0.15% move for profit

# --- Connect to MongoDB ---
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
entry_col = db[ENTRY_COLL]
chain_col = db[CHAIN_COLL]

# --- Load entry logic snapshots ---
entry_docs = list(entry_col.find({}))
if not entry_docs:
    print('No entry logic snapshots found!')
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
for doc in entry_docs:
    ts = doc.get('timestamp')
    if isinstance(ts, str):
        ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
    user = doc.get('user')
    expiry = doc.get('expiry')
    entry_direction = doc.get('entry_direction')
    entry_zone = doc.get('entry_zone', {})
    trade_type = doc.get('trade_type')
    entry_score = doc.get('entry_score')
    confidence = doc.get('confidence')
    must_avoid = doc.get('must_avoid')
    spot = entry_zone.get('zone_level') if entry_zone else None
    future_spot = get_future_spot(user, expiry, ts, LABEL_WINDOW_MINUTES)
    if spot is None or future_spot is None or entry_direction not in ['long', 'short', 'avoid']:
        continue
    spot_delta = (future_spot - spot) / spot * 100
    # Label: Correct if entry direction matches profitable move, or avoid in choppy market
    if entry_direction == 'long' and spot_delta > PROFIT_THRESHOLD:
        correct = 1
    elif entry_direction == 'short' and spot_delta < -PROFIT_THRESHOLD:
        correct = 1
    elif entry_direction == 'avoid' and abs(spot_delta) < PROFIT_THRESHOLD:
        correct = 1
    else:
        correct = 0
    row = {
        'timestamp': ts,
        'user': user,
        'expiry': expiry,
        'entry_direction': entry_direction,
        'trade_type': trade_type,
        'entry_score': entry_score,
        'confidence': confidence,
        'must_avoid': must_avoid,
        'zone_level': entry_zone.get('zone_level'),
        'zone_type': entry_zone.get('zone_type'),
        'zone_confidence': entry_zone.get('confidence'),
        'spot_delta': spot_delta,
        'correct': correct
    }
    rows.append(row)

# --- Save to CSV ---
df = pd.DataFrame(rows)
df.to_csv(EXPORT_CSV, index=False)
print(f'Exported {len(df)} labeled rows to {EXPORT_CSV}') 
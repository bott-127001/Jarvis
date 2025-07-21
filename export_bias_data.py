import pandas as pd
from pymongo import MongoClient
from datetime import datetime, timedelta
import os

# --- CONFIG ---
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = 'samarth'
BIAS_COLL = 'bias_identifier_snapshots'
CHAIN_COLL = 'option_chain_snapshots'
EXPORT_CSV = 'bias_identifier_snapshots_labeled.csv'
LABEL_WINDOW_MINUTES = 10
LABEL_THRESHOLD = 0.15  # 0.15% move for bullish/bearish

# --- Connect to MongoDB ---
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
bias_col = db[BIAS_COLL]
chain_col = db[CHAIN_COLL]

# --- Load bias snapshots ---
bias_docs = list(bias_col.find({}))
if not bias_docs:
    print('No bias snapshots found!')
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
for doc in bias_docs:
    ts = doc.get('timestamp')
    if isinstance(ts, str):
        ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
    user = doc.get('user')
    expiry = doc.get('expiry')
    spot = doc.get('spot')
    future_spot = get_future_spot(user, expiry, ts, LABEL_WINDOW_MINUTES)
    if spot is None or future_spot is None:
        continue
    spot_delta = (future_spot - spot) / spot * 100
    if spot_delta > LABEL_THRESHOLD:
        true_direction = 'Bullish'
    elif spot_delta < -LABEL_THRESHOLD:
        true_direction = 'Bearish'
    else:
        true_direction = 'Sideways'
    row = {
        'timestamp': ts,
        'user': user,
        'expiry': expiry,
        'ce_oi_pct': doc.get('rolling_pct', {}).get('call_oi'),
        'ce_iv_pct': doc.get('rolling_pct', {}).get('call_iv'),
        'ce_vol_pct': doc.get('rolling_pct', {}).get('call_volume'),
        'pe_oi_pct': doc.get('rolling_pct', {}).get('put_oi'),
        'pe_iv_pct': doc.get('rolling_pct', {}).get('put_iv'),
        'pe_vol_pct': doc.get('rolling_pct', {}).get('put_volume'),
        'spot_delta': doc.get('spot'),
        'price_direction': doc.get('price_direction'),
        'call_participant': doc.get('call_participant'),
        'put_participant': doc.get('put_participant'),
        'bias': doc.get('bias'),
        'true_direction': true_direction
    }
    rows.append(row)

# --- Save to CSV ---
df = pd.DataFrame(rows)
df.to_csv(EXPORT_CSV, index=False)
print(f'Exported {len(df)} labeled rows to {EXPORT_CSV}') 
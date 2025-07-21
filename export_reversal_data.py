import pandas as pd
from pymongo import MongoClient
from datetime import datetime, timedelta
import os
# --- CONFIG ---
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = 'samarth'
REV_COLL = 'reversal_probability_snapshots'
CHAIN_COLL = 'option_chain_snapshots'
EXPORT_CSV = 'reversal_probability_snapshots_labeled.csv'
LABEL_WINDOW_MINUTES = 10
REVERSAL_THRESHOLD = 0.15  # 0.15% move for reversal

# --- Connect to MongoDB ---
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
rev_col = db[REV_COLL]
chain_col = db[CHAIN_COLL]

# --- Load reversal snapshots ---
rev_docs = list(rev_col.find({}))
if not rev_docs:
    print('No reversal probability snapshots found!')
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
for doc in rev_docs:
    ts = doc.get('timestamp')
    if isinstance(ts, str):
        ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
    user = doc.get('user')
    expiry = doc.get('expiry')
    spot = doc.get('spot') if 'spot' in doc else None
    future_spot = get_future_spot(user, expiry, ts, LABEL_WINDOW_MINUTES)
    if spot is None or future_spot is None:
        continue
    spot_delta = (future_spot - spot) / spot * 100
    # Label: True Reversal if price direction changes by threshold
    reversal_type = doc.get('reversal_type')
    if reversal_type == 'bullish' and spot_delta > REVERSAL_THRESHOLD:
        true_reversal = 1
    elif reversal_type == 'bearish' and spot_delta < -REVERSAL_THRESHOLD:
        true_reversal = 1
    else:
        true_reversal = 0
    row = {
        'timestamp': ts,
        'user': user,
        'expiry': expiry,
        'bias_cluster_flipped': doc.get('bias_cluster_flipped'),
        'iv_oi_support_flip': doc.get('iv_oi_support_flip'),
        'price_vs_bias_conflict': doc.get('price_vs_bias_conflict'),
        'liquidity_ok': doc.get('liquidity_ok'),
        'structural_context': doc.get('structural_context'),
        'volatility_phase': doc.get('volatility_phase'),
        'market_style': doc.get('market_style'),
        'trap_detected': doc.get('trap_detected'),
        'reversal_probability': doc.get('reversal_probability'),
        'reversal_type': reversal_type,
        'spot_delta': spot_delta,
        'true_reversal': true_reversal
    }
    rows.append(row)

# --- Save to CSV ---
df = pd.DataFrame(rows)
df.to_csv(EXPORT_CSV, index=False)
print(f'Exported {len(df)} labeled rows to {EXPORT_CSV}') 
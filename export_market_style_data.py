import pandas as pd
from pymongo import MongoClient
from datetime import datetime, timedelta
import os
# --- CONFIG ---
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = 'samarth'
STYLE_COLL = 'market_style_snapshots'
CHAIN_COLL = 'option_chain_snapshots'
EXPORT_CSV = 'market_style_snapshots_labeled.csv'
LABEL_WINDOW_MINUTES = 10
TREND_THRESHOLD = 0.2  # 0.2% move for trending
SIDEWAYS_THRESHOLD = 0.1  # 0.1% range for sideways
VOLATILITY_IV = 5  # IV range for volatile

# --- Connect to MongoDB ---
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
style_col = db[STYLE_COLL]
chain_col = db[CHAIN_COLL]

# --- Load style snapshots ---
style_docs = list(style_col.find({}))
if not style_docs:
    print('No market style snapshots found!')
    exit(1)

# --- Helper: get spot/IV N min after timestamp ---
def get_future_spot_iv(user, expiry, ts, minutes=10):
    future_time = ts + timedelta(minutes=minutes)
    doc = chain_col.find_one({
        'user': user,
        'expiry': expiry,
        'timestamp': {'$gte': future_time}
    }, sort=[('timestamp', 1)])
    if doc and doc.get('strikes'):
        spot = doc['strikes'][0].get('underlying_spot_price')
        ce_iv = sum(r.get('call_iv', 0) or 0 for r in doc['strikes'] if r.get('call_option_type_zone') in ('ATM', 'OTM'))
        pe_iv = sum(r.get('put_iv', 0) or 0 for r in doc['strikes'] if r.get('put_option_type_zone') in ('ATM', 'OTM'))
        iv = ce_iv + pe_iv
        return spot, iv
    return None, None

# --- Build DataFrame ---
rows = []
for doc in style_docs:
    ts = doc.get('timestamp')
    if isinstance(ts, str):
        ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
    user = doc.get('user')
    expiry = doc.get('expiry')
    spot = doc.get('spot_trend_strength')  # Use spot_trend_strength as proxy for spot
    base_iv = doc.get('iv_diff')
    future_spot, future_iv = get_future_spot_iv(user, expiry, ts, LABEL_WINDOW_MINUTES)
    if spot is None or future_spot is None or base_iv is None or future_iv is None:
        continue
    spot_delta = (future_spot - spot) / (abs(spot) if spot else 1) * 100
    iv_range = abs(future_iv - base_iv)
    # Label logic
    if abs(spot_delta) > TREND_THRESHOLD and iv_range < VOLATILITY_IV:
        true_style = 'Trending'
    elif abs(spot_delta) < SIDEWAYS_THRESHOLD and iv_range < VOLATILITY_IV:
        true_style = 'Sideways'
    else:
        true_style = 'Volatile'
    row = {
        'timestamp': ts,
        'user': user,
        'expiry': expiry,
        'oi_diff': doc.get('oi_diff'),
        'vol_diff': doc.get('vol_diff'),
        'iv_diff': doc.get('iv_diff'),
        'price_direction': doc.get('price_direction'),
        'volatility_state': doc.get('volatility_state'),
        'spot_trend_strength': doc.get('spot_trend_strength'),
        'total_volume': doc.get('total_volume'),
        'total_oi': doc.get('total_oi'),
        'mode': doc.get('mode'),
        'true_style': true_style
    }
    rows.append(row)

# --- Save to CSV ---
df = pd.DataFrame(rows)
df.to_csv(EXPORT_CSV, index=False)
print(f'Exported {len(df)} labeled rows to {EXPORT_CSV}') 
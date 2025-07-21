import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import datetime
import os

# 1. Load data
CSV = 'market_style_snapshots_labeled.csv'
LOG = 'ml_logs/market_style_training.log'
MODEL = 'ml_models/market_style_model.pkl'
df = pd.read_csv(CSV)

# 2. Features and target
features = [
    'oi_diff', 'vol_diff', 'iv_diff',
    'price_direction', 'volatility_state',
    'spot_trend_strength', 'total_volume', 'total_oi', 'mode'
]
# Convert categorical features to numeric
for col in ['price_direction', 'volatility_state', 'mode']:
    if col in df:
        df[col] = df[col].astype('category').cat.codes
X = df[features]
y = df['true_style'].astype('category').cat.codes

# 3. Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 4. Train model
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)

# 5. Evaluate
y_pred = clf.predict(X_test)
report = classification_report(y_test, y_pred)
print(report)

# 6. Save model
os.makedirs('ml_models', exist_ok=True)
os.makedirs('ml_logs', exist_ok=True)
joblib.dump(clf, MODEL)

# 7. Log metrics
with open(LOG, 'a') as f:
    f.write(f'[{datetime.datetime.now()}] Training run for Market Style Identifier\n')
    f.write(report + '\n')
    f.write(f'Model saved to {MODEL}\n\n') 
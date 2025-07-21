import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import datetime

# 1. Load data
CSV = 'bias_identifier_snapshots_labeled.csv'
LOG = 'ml_logs/bias_training.log'
MODEL = 'ml_models/bias_identifier_model.pkl'
df = pd.read_csv(CSV)

# 2. Features and target
features = [
    'ce_oi_pct', 'ce_iv_pct', 'ce_vol_pct',
    'pe_oi_pct', 'pe_iv_pct', 'pe_vol_pct',
    'spot_delta', 'price_direction',
    'call_participant', 'put_participant', 'bias'
]
# Convert categorical features to numeric
for col in ['price_direction', 'call_participant', 'put_participant', 'bias']:
    if col in df:
        df[col] = df[col].astype('category').cat.codes
X = df[features]
y = df['true_direction'].astype('category').cat.codes

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
import os
os.makedirs('ml_models', exist_ok=True)
os.makedirs('ml_logs', exist_ok=True)
joblib.dump(clf, MODEL)

# 7. Log metrics
with open(LOG, 'a') as f:
    f.write(f'[{datetime.datetime.now()}] Training run for Bias Identifier\n')
    f.write(report + '\n')
    f.write(f'Model saved to {MODEL}\n\n') 
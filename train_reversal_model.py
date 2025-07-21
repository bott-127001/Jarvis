import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
import joblib
import datetime
import os

# 1. Load data
CSV = 'reversal_probability_snapshots_labeled.csv'
LOG = 'ml_logs/reversal_training.log'
MODEL = 'ml_models/reversal_probability_model.pkl'
df = pd.read_csv(CSV)

# 2. Features and target
features = [
    'bias_cluster_flipped', 'iv_oi_support_flip', 'price_vs_bias_conflict',
    'liquidity_ok', 'structural_context', 'volatility_phase',
    'market_style', 'trap_detected', 'reversal_probability', 'spot_delta'
]
# Convert categorical features to numeric
for col in ['structural_context', 'volatility_phase', 'market_style']:
    if col in df:
        df[col] = df[col].astype('category').cat.codes
X = df[features]
y = df['true_reversal']

# 3. Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 4. Train model
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)

# 5. Evaluate
y_pred = clf.predict(X_test)
y_prob = clf.predict_proba(X_test)[:, 1]
report = classification_report(y_test, y_pred)
roc = roc_auc_score(y_test, y_prob)
print(report)
print('ROC-AUC:', roc)

# 6. Save model
os.makedirs('ml_models', exist_ok=True)
os.makedirs('ml_logs', exist_ok=True)
joblib.dump(clf, MODEL)

# 7. Log metrics
with open(LOG, 'a') as f:
    f.write(f'[{datetime.datetime.now()}] Training run for Reversal Probability Finder\n')
    f.write(report + f'\nROC-AUC: {roc}\n')
    f.write(f'Model saved to {MODEL}\n\n') 
import pandas as pd
import xgboost as xgb
import joblib

# Load data
csv_path = "meta_model_training_data.csv"
df = pd.read_csv(csv_path)
X = df.drop("entry_worked", axis=1)
y = df["entry_worked"]

# Convert categorical features if needed
for col in X.columns:
    if X[col].dtype == object:
        X[col] = X[col].astype('category').cat.codes

model = xgb.XGBClassifier(n_estimators=100, max_depth=4, use_label_encoder=False, eval_metric='logloss')
model.fit(X, y)
joblib.dump(model, "ml_models/meta_model.pkl")
print("Meta-model trained and saved as ml_models/meta_model.pkl") 
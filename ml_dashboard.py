import streamlit as st
import os
import pandas as pd
import plotly.express as px
from pymongo import MongoClient
from datetime import datetime
import requests

st.set_page_config(page_title='ML Model Monitoring Dashboard', layout='wide')
st.title('ML Model Monitoring & Evaluation Dashboard')

# --- MongoDB Connection ---
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client["samarth"]

MODULES = [
    ('bias_identifier_snapshots', 'Bias Identifier'),
    ('market_style_snapshots', 'Market Style Identifier'),
    ('trap_detector_snapshots', 'Trap Detector'),
    ('reversal_probability_snapshots', 'Reversal Probability Finder'),
    ('support_resistance_snapshots', 'Support/Resistance Guard'),
    ('entry_logic_snapshots', 'Entry Logic Engine'),
]

# --- Helper: Load DataFrame from MongoDB ---
def load_df(col, limit=1000):
    data = list(db[col].find().sort("timestamp", -1).limit(limit))
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    if 'timestamp' in df:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

# --- Tabs for Dashboard Sections ---
tabs = st.tabs([
    "Signal Accuracy",
    "Confidence vs Outcome",
    "Anomaly Rate",
    "Entry Win/Loss Streaks",
    "Module Alerts",
    "Model Retraining",
    "Trade Replay (Time Machine)"
])

# --- 1. Signal Accuracy by Module ---
with tabs[0]:
    st.header("Historical Signal Accuracy by Module")
    for col, label in MODULES:
        df = load_df(col)
        st.subheader(label)
        if df.empty:
            st.info("No data available.")
            continue
        # Assume 'outcome' field exists (True/False for correct/incorrect), else dummy
        if 'outcome' in df:
            acc = df['outcome'].mean()
            st.metric("Accuracy", f"{acc*100:.1f}%")
            st.line_chart(df.set_index('timestamp')['outcome'])
        else:
            st.warning("No outcome labels found. Showing count of records.")
            st.bar_chart(df.set_index('timestamp').resample('1H').size())

# --- 2. Model Confidence vs Outcome Heatmap ---
with tabs[1]:
    st.header("Model Confidence vs Outcome Heatmap (Entry Logic)")
    df = load_df('entry_logic_snapshots')
    if not df.empty and 'confidence' in df:
        # Dummy: if 'outcome' missing, simulate
        if 'outcome' not in df:
            import numpy as np
            df['outcome'] = (df['confidence'].astype(str).str.contains('high')).astype(int)  # Dummy: treat 'high' as win
        fig = px.density_heatmap(df, x='confidence', y='outcome', nbinsx=10, nbinsy=2, color_continuous_scale='Viridis', labels={'outcome':'Win (1) / Loss (0)'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough data for heatmap.")

# --- 3. Anomaly Rate Tracking ---
with tabs[2]:
    st.header("Anomaly Rate Tracking")
    df = load_df('anomaly_log', limit=2000)
    if not df.empty:
        df['date'] = df['timestamp'].dt.date
        anomaly_rate = df.groupby('date')['anomaly_detected'].mean()
        st.line_chart(anomaly_rate)
        st.write("Recent Anomalies:")
        st.dataframe(df.sort_values('timestamp', ascending=False)[['timestamp','anomaly_score','anomaly_detected','anomaly_reason']].head(10))
    else:
        st.info("No anomaly logs found.")

# --- 4. Entry Win/Loss Streak Tracker ---
with tabs[3]:
    st.header("Entry Win/Loss Streak Tracker")
    df = load_df('entry_logic_snapshots')
    if not df.empty:
        # Dummy: if 'outcome' missing, simulate
        if 'outcome' not in df:
            df['outcome'] = (df['confidence'].astype(str).str.contains('high')).astype(int)
        streaks = []
        last = None
        count = 0
        for val in df['outcome']:
            if val == last:
                count += 1
            else:
                if last is not None:
                    streaks.append((last, count))
                last = val
                count = 1
        if last is not None:
            streaks.append((last, count))
        win_streak = max((c for v, c in streaks if v == 1), default=0)
        loss_streak = max((c for v, c in streaks if v == 0), default=0)
        st.metric("Longest Win Streak", win_streak)
        st.metric("Longest Loss Streak", loss_streak)
        st.write("Recent Outcomes:")
        st.bar_chart(df.set_index('timestamp')['outcome'].head(50))
    else:
        st.info("No entry logic data found.")

# --- 5. Module Failure Auto-Alert ---
with tabs[4]:
    st.header("Module Failure Auto-Alert")
    alert_msgs = []
    for col, label in MODULES:
        df = load_df(col)
        if df.empty:
            continue
        # Dummy: if 'outcome' missing, simulate
        if 'outcome' not in df:
            continue
        # Check for 3+ consecutive failures (outcome==0)
        fails = (df['outcome'] == 0).astype(int)
        streak = 0
        for f in fails:
            if f:
                streak += 1
                if streak >= 3:
                    alert_msgs.append(f"{label}: {streak} consecutive failures!")
                    break
            else:
                streak = 0
    if alert_msgs:
        for msg in alert_msgs:
            st.error(msg)
    else:
        st.success("No module has crossed the failure threshold.")

# --- 6. Model Retraining Tab ---
with tabs[5]:
    st.header("Model Retraining & Status")
    retrain_log = list(db["model_retrain_log"].find().sort("timestamp", -1).limit(50))
    df_log = pd.DataFrame(retrain_log)
    modules = [m[0].replace('_snapshots','') for m in MODULES]
    for module in modules:
        st.subheader(module)
        mod_log = df_log[df_log["module"] == module]
        if not mod_log.empty:
            last = mod_log.iloc[0]
            st.write(f"Last retrain: {last['timestamp']}")
            st.write(f"Accuracy: {last['accuracy'] if pd.notnull(last['accuracy']) else 'N/A'}")
            st.write(f"Sample count: {last['sample_count']}")
            if last.get('feature_importances') is not None:
                st.write("Feature Importances:")
                st.bar_chart(pd.Series(last['feature_importances']))
            if st.button(f"Retrain {module}"):
                with st.spinner("Retraining..."):
                    try:
                        resp = requests.post(f"http://localhost:8001/retrain-module", params={"module": module})
                        st.success(str(resp.json()))
                    except Exception as e:
                        st.error(str(e))
        else:
            st.write("No retrain log found.")
    st.write("Recent Retrain Logs:")
    if not df_log.empty:
        st.dataframe(df_log[["timestamp","module","accuracy","sample_count","error"]].head(20))
    else:
        st.info("No retrain logs yet.")

# --- 7. Trade Replay (Time Machine) Tab ---
with tabs[6]:
    st.header("Trade Replay (Time Machine)")
    journal = list(db["trade_journal"].find().sort("timestamp", -1).limit(200))
    if not journal:
        st.info("No journal entries found.")
    else:
        df_journal = pd.DataFrame(journal)
        df_journal["timestamp"] = pd.to_datetime(df_journal["timestamp"])
        selected = st.selectbox("Select a trade to replay", df_journal["timestamp"].astype(str))
        trade = df_journal[df_journal["timestamp"].astype(str) == selected].iloc[0]
        st.write(f"**Timestamp:** {trade['timestamp']}")
        st.write(f"**Entry Direction:** {trade['entry_direction']}")
        st.write(f"**Recommended Size:** {trade['recommended_position_size']}")
        st.write(f"**Meta-Model Decision:** {trade['meta_model_decision']} (p={trade['meta_model_probability']:.2f})")
        st.write(f"**Must Avoid:** {trade['must_avoid']}")
        st.write(f"**Reason:** {trade['reason']}")
        st.write(f"**Outcome:** {trade.get('outcome', 'N/A')}")
        st.write(f"**Modules Triggered:** {', '.join(trade['modules_triggered'])}")
        st.write("**Module Outputs:**")
        st.json(trade["raw_signals"])
        # Optional: next/prev navigation
        idx = df_journal.index[df_journal["timestamp"].astype(str) == selected][0]
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Previous") and idx < len(df_journal) - 1:
                st.experimental_set_query_params(trade_idx=idx + 1)
        with col2:
            if st.button("Next") and idx > 0:
                st.experimental_set_query_params(trade_idx=idx - 1)

st.caption("All statistics are for recent data only. For full analytics, connect to the database and export as needed.") 
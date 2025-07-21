import streamlit as st
import os

st.set_page_config(page_title='ML Model Monitoring Dashboard', layout='wide')

st.title('ML Model Monitoring Dashboard')

MODULES = [
    ('bias', 'Bias Identifier'),
    ('market_style', 'Market Style Identifier'),
    ('trap', 'Trap Detector'),
    ('reversal', 'Reversal Probability Finder'),
    ('sr', 'Support/Resistance Guard'),
    ('entry_logic', 'Entry Logic Engine'),
]

for module, label in MODULES:
    log_file = f'ml_logs/{module}_training.log'
    st.header(f'{label} Model')
    if os.path.exists(log_file):
        with open(log_file) as f:
            lines = f.readlines()
            st.text(''.join(lines[-20:]))  # Show last 20 lines (latest run)
    else:
        st.warning(f'No log file found for {label}.') 
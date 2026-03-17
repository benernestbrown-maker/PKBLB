import streamlit as st
import pandas as pd
import numpy as np

# Page Config for a professional look
st.set_page_config(page_title="Ben's Elite PT Hub", layout="wide")

# The Link (Entire Document)
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRcgV5PFrp4XmAcNn3cutN0PvxKoZGhTY8wc8NKp70wDdajdsrYPOfNWezEBCoX-wSJyGtHSDDMyqse/pub?output=csv"

@st.cache_data(ttl=60)
def get_data():
    # Load raw data
    raw_df = pd.read_csv(CSV_URL, skiprows=4)
    raw_df.columns = [str(c).replace('\n', ' ').strip() for c in raw_df.columns]
    return raw_df.dropna(subset=['DATE'])

try:
    df = get_data()
    latest = df.dropna(subset=['BODYWEIGHT (kg)']).iloc[-1]

    st.title("⚡ Ben's Performance Command Centre")

    # Creating Tabs for a cleaner 'App' experience
    tab1, tab2, tab3 = st.tabs(["📊 Daily Dashboard", "🏋️ Training Log", "😴 Recovery & Oura"])

    with tab1:
        # --- TOP METRICS ---
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Weight", f"{latest['BODYWEIGHT (kg)']} kg")
        
        step_count = int(float(str(latest['STEPS']).replace(',', '')))
        m2.metric("Steps", f"{step_count:,}", f"{step_count - 12500} vs Goal")
        
        m3.metric("Energy", f"{latest['ENERGY LEVELS Scale 1-10']}/10")
        m4.metric("Stress", f"{latest['STRESS LEVELS Scale 1-10']}/10")

        st.divider()

        # --- TRENDS ---
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("Weight Trend")
            st.line_chart(df.set_index('DATE')['BODYWEIGHT (kg)'])
        with col_b:
            st.subheader("Activity Levels")
            df['STEPS_NUM'] = pd.to_numeric(df['STEPS'].astype(str).str.replace(',', ''), errors='coerce')
            st.bar_chart(df.set_index('DATE')['STEPS_NUM'])

    with tab2:
        st.subheader("Recent Training Execution")
        # Pulling session quality data
        training_df = df[['DATE', 'RESISTANCE TRAINING', 'SESSION EXECUTION', 'MOTIVATION TO TRAIN Scale 1-10']].dropna(subset=['RESISTANCE TRAINING'])
        st.dataframe(training_df.tail(10), use_container_width=True)
        
    with tab3:
        st.subheader("Oura Recovery Markers")
        # Pulling biometrics
        recovery_df = df[['DATE', 'RHR (bpm)', 'HRV (ms)', 'READINESS READING', 'SLEEP QUALITY Sleep Score OR Scale 1-10']].dropna(subset=['HRV (ms)'])
        
        col_c, col_d = st.columns(2)
        with col_c:
            st.line_chart(recovery_df.set_index('DATE')[['HRV (ms)', 'RHR (bpm)']])
        with col_d:
            st.line_chart(recovery_df.set_index('DATE')['READINESS READING'])

    # --- FOOTER: PT COMMENTS ---
    st.divider()
    st.subheader("💬 Latest Check-in Notes")
    notes = df[['DATE', 'DAILY COMMENTS']].dropna().tail(3)
    for _, row in notes.iterrows():
        with st.chat_message("user"):
            st.write(f"**{row['DATE']}:** {row['DAILY COMMENTS']}")

except Exception as e:
    st.error(f"Waiting for your spreadsheet to update... (Or check column names). Error: {e}")

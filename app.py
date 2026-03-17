import streamlit as st
import pandas as pd
import numpy as np

# Page setup for a pro fitness app look
st.set_page_config(page_title="Performance Command Centre", layout="wide")

# Replace this with your base "Entire Document" link (remove everything after /pub?)
BASE_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRcgV5PFrp4XmAcNn3cutN0PvxKoZGhTY8wc8NKp70wDdajdsrYPOfNWezEBCoX-wSJyGtHSDDMyqse/pub?"

# --- TAB IDS (Check these in your browser URL) ---
TRACKER_GID = "0"          # Usually 0 for the first tab
OURA_GID = "1547806509"    # Example GID for Oura tab - update if different

@st.cache_data(ttl=60)
def load_sheet(gid, skip=0):
    url = f"{BASE_URL}gid={gid}&single=true&output=csv"
    df = pd.read_csv(url, skiprows=skip)
    df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
    return df

try:
    # Load the primary tracker
    # We skip 4 rows to get to your headers (Date, Bodyweight, etc.)
    df = load_sheet(TRACKER_GID, skip=4)
    df = df.dropna(subset=['DATE'])
    
    # Header Section
    st.title("🚀 Ben's Performance Hub")
    
    # Navigation Sidebar
    page = st.sidebar.radio("Navigate", ["Daily Dashboard", "Recovery (Oura)", "Training Log"])

    if page == "Daily Dashboard":
        # Get latest data
        latest = df.dropna(subset=['BODYWEIGHT (kg)']).iloc[-1]
        
        # Top Row Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Current Weight", f"{latest['BODYWEIGHT (kg)']} kg")
        
        step_val = int(float(str(latest['STEPS']).replace(',', ''))) if not pd.isna(latest['STEPS']) else 0
        m2.metric("Steps", f"{step_val:,}", f"{step_val - 12500} vs Goal")
        
        m3.metric("Energy", f"{latest['ENERGY LEVELS Scale 1-10']}/10")
        m4.metric("Sleep Quality", f"{latest['SLEEP QUALITY Sleep Score OR Scale 1-10']}")

        st.divider()
        
        # Charts
        c_left, c_right = st.columns(2)
        with c_left:
            st.subheader("Weight Trend")
            st.line_chart(df.set_index('DATE')['BODYWEIGHT (kg)'])
        with c_right:
            st.subheader("Activity")
            df['STEPS_NUM'] = pd.to_numeric(df['STEPS'].astype(str).str.replace(',', ''), errors='coerce')
            st.bar_chart(df.set_index('DATE')['STEPS_NUM'])

    elif page == "Recovery (Oura)":
        st.subheader("Biometric Recovery (Oura)")
        # Load Oura data (no skip needed usually for raw CSV links)
        oura_df = load_sheet(OURA_GID)
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("Average HRV")
            st.line_chart(oura_df.set_index('day')['average_hrv'])
        with col2:
            st.write("Readiness Score")
            st.area_chart(oura_df.set_index('day')['readiness_score'])

    elif page == "Training Log":
        st.subheader("Recent Sessions")
        log_df = df[['DATE', 'RESISTANCE TRAINING', 'SESSION EXECUTION', 'DAILY COMMENTS']].dropna(subset=['RESISTANCE TRAINING'])
        st.table(log_df.tail(10))

except Exception as e:
    st.error(f"Error: {e}")
    st.info("Check if your 'Daily Tracker' tab is actually the first tab (gid=0).")

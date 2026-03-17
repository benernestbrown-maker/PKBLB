import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Elite PT Dashboard", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for a "Dark Mode" Fitness App vibe
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { color: #00ffcc; }
    </style>
    """, unsafe_allow_html=True)

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRcgV5PFrp4XmAcNn3cutN0PvxKoZGhTY8wc8NKp70wDdajdsrYPOfNWezEBCoX-wSJyGtHSDDMyqse/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=600)
def load_and_clean():
    df = pd.read_csv(CSV_URL, skiprows=4)
    df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
    df = df.dropna(subset=['DATE'])
    # Convert numeric columns safely
    for col in ['BODYWEIGHT (kg)', 'STEPS', 'CALORIES (kcals)']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
    return df

try:
    df = load_and_clean()
    latest = df.dropna(subset=['BODYWEIGHT (kg)']).iloc[-1]
    
    st.title("⚡ Ben's Performance Hub")
    
    # --- TOP ROW: VITAL METRICS ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Current Weight", f"{latest['BODYWEIGHT (kg)']} kg")
    
    # Calculate step delta vs your 12,500 target
    step_val = int(latest['STEPS']) if not np.isnan(latest['STEPS']) else 0
    m2.metric("Steps", f"{step_val:,}", f"{step_val - 12500} vs Goal")
    
    # Calories
    cal_val = latest['CALORIES (kcals)'] if 'CALORIES (kcals)' in latest else 0
    m3.metric("Energy Level", f"{latest['ENERGY LEVELS Scale 1-10']}/10")
    m4.metric("Sleep Quality", f"{latest['SLEEP QUALITY Sleep Score OR Scale 1-10']}")

    st.divider()

    # --- MIDDLE ROW: THE GRAPHS ---
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("📉 Weight vs. Steps")
        # Creating a combined view
        st.line_chart(df.set_index('DATE')[['BODYWEIGHT (kg)', 'STEPS']], y=['BODYWEIGHT (kg)'])
        st.caption("Tracking how activity impacts your weight trend.")

    with col_b:
        st.subheader("🔥 Fuel & Focus")
        # Bar chart for energy levels vs stress
        stress_cols = ['ENERGY LEVELS Scale 1-10', 'STRESS LEVELS Scale 1-10']
        st.bar_chart(df.set_index('DATE')[stress_cols])

    # --- BOTTOM ROW: DATA TABLE FOR PT ---
    with st.expander("View Raw Weekly Log"):
        st.dataframe(df.tail(7), use_container_width=True)

except Exception as e:
    st.error(f"Link Active, but data format issue: {e}")

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. UI Architecture
st.set_page_config(page_title="Ben's Intelligence Hub", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { color: #00ffcc; font-size: 2.2rem; font-weight: 800; }
    .stPlotlyChart { border: 1px solid #30363d; border-radius: 12px; background-color: #161b22; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Expert Data Connector
# UPDATE THESE GIDs based on your spreadsheet URLs
TRACKER_GID = "0"
INBODY_GID = "1795026937" 
OURA_GID = "1547806509"

BASE_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRcgV5PFrp4XmAcNn3cutN0PvxKoZGhTY8wc8NKp70wDdajdsrYPOfNWezEBCoX-wSJyGtHSDDMyqse/pub?"

@st.cache_data(ttl=60)
def fetch_tab(gid, skip_rows=0):
    url = f"{BASE_URL}gid={gid}&single=true&output=csv"
    try:
        df = pd.read_csv(url, skiprows=skip_rows)
        df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Tab ID {gid} Error: {e}")
        return pd.DataFrame()

def process_dates(df, date_col):
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
        df = df.dropna(subset=[date_col])
        # Expert Filter: Purge future-dated empty rows
        df = df[df[date_col] <= datetime.now()]
    return df

try:
    # --- DATA ACQUISITION ---
    raw_tracker = fetch_tab(TRACKER_GID, skip_rows=4)
    tracker_df = process_dates(raw_tracker, 'DATE')
    
    inbody_df = process_dates(fetch_tab(INBODY_GID, skip_rows=2), 'DATE')
    oura_df = process_dates(fetch_tab(OURA_GID), 'day')

    # --- SIDEBAR: TIME INTELLIGENCE ---
    st.sidebar.title("📈 Time Controls")
    time_choice = st.sidebar.selectbox(
        "Select Visual Window", 
        ["Week", "Month", "3 Months", "6 Months", "12 Months", "All Time"]
    )
    
    windows = {"Week": 7, "Month": 30, "3 Months": 90, "6 Months": 180, "12 Months": 365, "All Time": 9999}
    latest_date = tracker_df['DATE'].max()
    start_date = latest_date - timedelta(days=windows[time_choice])
    
    # Filter views
    df_v = tracker_df[tracker_df['DATE'] >= start_date]
    ib_v = inbody_df[inbody_df['DATE'] >= start_date]
    ou_v = oura_df[oura_df['day'] >= start_date]

    # --- TOP ROW: HUD ---
    st.title("⚡ PERFORMANCE COMMAND CENTRE")
    latest = tracker_df.dropna(subset=['BODYWEIGHT (kg)']).iloc[-1]
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Bodyweight", f"{latest['BODYWEIGHT (kg)']} kg")
    
    steps = int(pd.to_numeric(str(latest['STEPS']).replace(',', ''), errors='coerce'))
    c2.metric("Steps", f"{steps:,}", f"{steps - 12500} vs Goal")
    c3.metric("Energy", f"{latest['ENERGY LEVELS Scale 1-10']}/10")
    c4.metric("Sleep", f"{latest['SLEEP QUALITY Sleep Score OR Scale 1-10']}")

    st.divider()

    # --- DATA TABS ---
    t_comp, t_act, t_rec = st.tabs(["📉 Composition", "🏃 Activity", "😴 Recovery"])

    with t_comp:
        # Weight Trend
        fig_w = go.Figure()
        fig_w.add_trace(go.Scatter(x=df_v['DATE'], y=df_v['BODYWEIGHT (kg)'], line=dict(color='#00ffcc', width=4, shape='spline'), mode='lines+markers'))
        fig_w.update_layout(template="plotly_dark", title=f"Weight Trend ({time_choice})", height=400, margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig_w, use_container_width=True)
        
        # InBody Metrics
        col1, col2 = st.columns(2)
        if not ib_v.empty:
            with col1:
                fig_bf = go.Figure(go.Scatter(x=ib_v['DATE'], y=ib_v['BF%'], line=dict(color='#FF4B4B', width=3)))
                fig_bf.update_layout(template="plotly_dark", title="Body Fat %", height=300)
                st.plotly_chart(fig_bf, use_container_width=True)
            with col2:
                fig_mm = go.Figure(go.Scatter(x=ib_v['DATE'], y=ib_v['MUSCLE MASS'], line=dict(color='#00FFAA', width=3)))
                fig_mm.update_layout(template="plotly_dark", title="Muscle Mass (kg)", height=300)
                st.plotly_chart(fig_mm, use_container_width=True)

    with t_act:
        fig_s = go.Figure(go.Bar(x=df_v['DATE'], y=pd.to_numeric(df_v['STEPS'].astype(str).str.replace(',', ''), errors='coerce'), marker_color='#00ffcc'))
        fig_s.add_hline(y=12500, line_dash="dash", line_color="white")
        fig_s.update_layout(template="plotly_dark", title="Daily Step Activity", height=400)
        st.plotly_chart(fig_s, use_container_width=True)

    with t_rec:
        if not ou_v.empty:
            fig_h = go.Figure()
            fig_h.add_trace(go.Scatter(x=ou_v['day'], y=ou_v['average_hrv'], name="HRV", line=dict(color='#00ffcc', width=3)))
            fig_h.add_trace(go.Scatter(x=ou_v['day'], y=ou_v['readiness_score'], name="Readiness", line=dict(color='#FF4B4B', width=2, dash='dot')))
            fig_h.update_layout(template="plotly_dark", title="Oura Recovery Trends", height=400)
            st.plotly_chart(fig_h, use_container_width=True)

    # --- COACHING FEEDBACK ---
    st.divider()
    with st.expander("📝 Latest Daily Comments"):
        notes = df_v.dropna(subset=['DAILY COMMENTS']).tail(5)
        for _, row in notes.iterrows():
            st.info(f"**{row['DATE'].strftime('%d %b')}:** {row['DAILY COMMENTS']}")

except Exception as e:
    st.error(f"Intelligence Module Error: {e}")

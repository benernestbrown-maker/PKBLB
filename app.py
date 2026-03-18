import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. Dashboard Architecture
st.set_page_config(page_title="Ben's Intelligence Hub", layout="wide")

# Premium Dark UI Styling
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { color: #00ffcc; font-size: 2.2rem; font-weight: 800; }
    .stPlotlyChart { border: 1px solid #30363d; border-radius: 12px; background-color: #161b22; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

# GIDs - Ensure these match your sheet tabs
TRACKER_GID = "0"
OURA_GID = "1547806509"
BASE_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRcgV5PFrp4XmAcNn3cutN0PvxKoZGhTY8wc8NKp70wDdajdsrYPOfNWezEBCoX-wSJyGtHSDDMyqse/pub?"

@st.cache_data(ttl=60)
def fetch_decisive_data():
    # Load Daily Tracker
    t_url = f"{BASE_URL}gid={TRACKER_GID}&single=true&output=csv"
    df = pd.read_csv(t_url, skiprows=4)
    df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
    df['DATE'] = pd.to_datetime(df['DATE'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['DATE'])
    # Kills future 'scribble' by capping at today
    df = df[df['DATE'] <= datetime.now()]
    
    # Decisive Tracker Metrics
    for col in ['BODYWEIGHT (kg)', 'STEPS']:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
    
    # Load Oura Data
    o_url = f"{BASE_URL}gid={OURA_GID}&single=true&output=csv"
    oura = pd.read_csv(o_url)
    oura.columns = [str(c).strip() for c in oura.columns]
    oura['day'] = pd.to_datetime(oura['day'], errors='coerce')
    oura = oura[oura['day'] <= datetime.now()]
    
    return df, oura

def build_pro_chart(df, x_col, y_col, title, color, timeframe, is_bar=False):
    data = df.dropna(subset=[y_col])
    if data.empty: return
    
    fig = go.Figure()
    if is_bar:
        fig.add_trace(go.Bar(x=data[x_col], y=data[y_col], marker_color=color, opacity=0.8))
    else:
        fig.add_trace(go.Scatter(x=data[x_col], y=data[y_col], 
                                 line=dict(color=color, width=4, shape='spline'),
                                 mode='lines+markers', marker=dict(size=8)))
    
    fig.update_layout(
        template="plotly_dark", title=f"<b>{title}</b>",
        height=380, margin=dict(l=10, r=10, t=50, b=10),
        hovermode="x unified", showlegend=False,
        xaxis=dict(showgrid=False), yaxis=dict(gridcolor='rgba(255,255,255,0.05)')
    )
    st.plotly_chart(fig, use_container_width=True)

try:
    df, oura = fetch_decisive_data()
    
    # --- SIDEBAR: TIME CONTROLS ---
    st.sidebar.title("📈 Time Intelligence")
    time_choice = st.sidebar.selectbox(
        "Select Visual Window", 
        ["Week", "Month", "3 Months", "6 Months", "12 Months", "All Time"]
    )
    
    windows = {"Week": 7, "Month": 30, "3 Months": 90, "6 Months": 180, "12 Months": 365, "All Time": 9999}
    latest_date = df['DATE'].max()
    start_date = latest_date - timedelta(days=windows[time_choice])
    
    # Filtered Views
    df_v = df[df['DATE'] >= start_date]
    ou_v = oura[oura['day'] >= start_date]

    st.title("⚡ PERFORMANCE COMMAND CENTRE")

    # --- TABS: THE DECISIVE STACK ---
    t_over, t_comp, t_rec, t_time = st.tabs(["📊 Key Vitals", "📉 Composition", "😴 Oura Recovery", "📅 Master Timeline"])

    with t_over:
        # Latest Snapshot
        lw = df.dropna(subset=['BODYWEIGHT (kg)']).iloc[-1]
        lo = oura.dropna(subset=['readiness_score']).iloc[-1]
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Current Weight", f"{lw['BODYWEIGHT (kg)']} kg")
        s_val = int(lw['STEPS']) if not pd.isna(lw['STEPS']) else 0
        c2.metric("Latest Steps", f"{s_val:,}", f"{s_val - 12500} vs Goal")
        c3.metric("Oura Readiness", f"{int(lo['readiness_score'])}")
        c4.metric("Sleep Score", f"{int(lo['score_sleep'])}")
        
        st.divider()
        build_pro_chart(df_v, 'DATE', 'BODYWEIGHT (kg)', "Weight Snapshot", "#00ffcc", time_choice)

    with t_comp:
        build_pro_chart(df_v, 'DATE', 'BODYWEIGHT (kg)', "Bodyweight Progress (kg)", "#00ffcc", time_choice)
        st.info("💡 Next step: Mapping InBody GID for Body Fat % and Muscle Mass trends.")

    with t_rec:
        build_pro_chart(ou_v, 'day', 'average_hrv', "Heart Rate Variability (HRV)", "#00ffcc", time_choice)
        build_pro_chart(ou_v, 'readiness_score', "Readiness Trend", "#FF4B4B", time_choice)
        build_pro_chart(ou_v, 'score_sleep', "Sleep Performance", "#9C27B0", time_choice)

    with t_time:
        st.subheader(f"Full Performance History ({time_choice})")
        build_pro_chart(df_v, 'DATE', 'STEPS', "Daily Activity (Steps)", "#FF4B4B", time_choice, is_bar=True)
        build_pro_chart(ou_v, 'day', 'average_hrv', "Biological Recovery (HRV)", "#00ffcc", time_choice)
        build_pro_chart(ou_v, 'day', 'score_sleep', "Decisive Sleep Trends", "#9C27B0", time_choice)

except Exception as e:
    st.error(f"Waiting for Data Sync... Error: {e}")

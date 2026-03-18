import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. Expert UI Configuration
st.set_page_config(page_title="Performance Intelligence Hub", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { color: #00ffcc; font-size: 2.2rem; font-weight: 800; }
    .stPlotlyChart { border: 1px solid #30363d; border-radius: 12px; background-color: #161b22; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

# GIDs - Essential for Multi-Tab access
TRACKER_GID = "0"
OURA_GID = "1547806509"
BASE_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRcgV5PFrp4XmAcNn3cutN0PvxKoZGhTY8wc8NKp70wDdajdsrYPOfNWezEBCoX-wSJyGtHSDDMyqse/pub?"

@st.cache_data(ttl=60)
def fetch_performance_data():
    # Fetch Daily Tracker
    t_url = f"{BASE_URL}gid={TRACKER_GID}&single=true&output=csv"
    df = pd.read_csv(t_url, skiprows=4)
    df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
    df['DATE'] = pd.to_datetime(df['DATE'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['DATE'])
    df = df[df['DATE'] <= datetime.now()]
    
    # Clean Tracker Metrics
    for col in ['BODYWEIGHT (kg)', 'STEPS']:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
    
    # Fetch Oura Decisive Data
    o_url = f"{BASE_URL}gid={OURA_GID}&single=true&output=csv"
    oura = pd.read_csv(o_url)
    oura.columns = [str(c).strip() for c in oura.columns]
    oura['day'] = pd.to_datetime(oura['day'], errors='coerce')
    
    # Ensure Oura data is also capped at today
    oura = oura[oura['day'] <= datetime.now()]
    
    return df, oura

def render_decisive_chart(df, x_col, y_col, title, color, is_bar=False):
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
        height=350, margin=dict(l=10, r=10, t=50, b=10),
        hovermode="x unified", showlegend=False,
        xaxis=dict(showgrid=False), yaxis=dict(gridcolor='rgba(255,255,255,0.05)')
    )
    st.plotly_chart(fig, use_container_width=True)

try:
    df, oura = fetch_performance_data()
    
    # --- SIDEBAR: TIMELINE CONTROLS ---
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

    # --- TABS: DECISIVE DATA ONLY ---
    t_over, t_comp, t_rec, t_time = st.tabs(["📊 Key Vitals", "📉 Composition", "😴 Oura Recovery", "📅 Master Timeline"])

    with t_over:
        latest_w = df.dropna(subset=['BODYWEIGHT (kg)']).iloc[-1]
        latest_o = oura.dropna(subset=['readiness_score']).iloc[-1]
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Weight", f"{latest_w['BODYWEIGHT (kg)']} kg")
        
        s_val = int(latest_w['STEPS']) if not pd.isna(latest_w['STEPS']) else 0
        c2.metric("Steps", f"{s_val:,}", f"{s_val - 12500} vs Goal")
        
        c3.metric("Oura Readiness", f"{int(latest_o['readiness_score'])}")
        c4.metric("Sleep Score", f"{int(latest_o['score_sleep'])}")
        
        st.divider()
        render_decisive_chart(df_v, 'DATE', 'BODYWEIGHT (kg)', "Weight Trend", "#00ffcc")

    with t_comp:
        render_decisive_chart(df_v, 'DATE', 'BODYWEIGHT (kg)', "Bodyweight (kg)", "#00ffcc")
        st.info("💡 Decisive InBody Metrics (BF%/Muscle) will be mapped here next.")

    with t_rec:
        render_decisive_chart(ou_v, 'day', 'average_hrv', "Heart Rate Variability (HRV)", "#00ffcc")
        render_decisive_chart(ou_v, 'readiness_score', "Oura Readiness Score", "#FF4B4B")
        render_decisive_chart(ou_v, 'score_sleep', "Oura Sleep Score", "#9C27B0")

    with t_time:
        st.subheader("Full Performance Timeline")
        render_decisive_chart(df_v, 'DATE', 'STEPS', "Daily Activity (Steps)", "#FF4B4B", is_bar=True)
        render_decisive_chart(ou_v, 'day', 'average_hrv', "Recovery Trend (HRV)", "#00ffcc")
        render_decisive_chart(ou_v, 'day', 'score_sleep', "Sleep Quality Trend", "#9C27B0")

except Exception as e:
    st.error(f"Intelligence Module Error: {e}")

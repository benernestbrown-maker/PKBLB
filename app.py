import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. Dashboard Architecture
st.set_page_config(page_title="Ben's Performance Hub", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { color: #00ffcc; font-size: 2.2rem; font-weight: 800; }
    .stPlotlyChart { border: 1px solid #30363d; border-radius: 8px; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRcgV5PFrp4XmAcNn3cutN0PvxKoZGhTY8wc8NKp70wDdajdsrYPOfNWezEBCoX-wSJyGtHSDDMyqse/pub?output=csv"

@st.cache_data(ttl=60)
def get_clean_data():
    df = pd.read_csv(CSV_URL, skiprows=4)
    df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
    
    # Convert DATE to actual datetime objects
    df['DATE'] = pd.to_datetime(df['DATE'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['DATE'])
    
    # Define metrics and clean numeric data
    metrics = {
        'Weight': 'BODYWEIGHT (kg)',
        'Steps': 'STEPS',
        'Energy': 'ENERGY LEVELS Scale 1-10',
        'Sleep': 'SLEEP QUALITY Sleep Score OR Scale 1-10',
        'Stress': 'STRESS LEVELS Scale 1-10'
    }
    for col in metrics.values():
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
    
    # CRITICAL: Filter out any data from the future to stop the 'scribble'
    df = df[df['DATE'] <= datetime.now()]
    return df, metrics

def render_chart(df, col, title, color, timeframe_label):
    if df[col].dropna().empty: return
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['DATE'], y=df[col],
        name=title, line=dict(color=color, width=3, shape='spline'),
        mode='lines+markers', marker=dict(size=6)
    ))
    
    fig.update_layout(
        template="plotly_dark", title=f"<b>{title} - {timeframe_label}</b>",
        height=350, margin=dict(l=10, r=10, t=40, b=10),
        hovermode="x unified", showlegend=False,
        xaxis=dict(showgrid=False), yaxis=dict(gridcolor='rgba(255,255,255,0.05)')
    )
    st.plotly_chart(fig, use_container_width=True)

try:
    full_df, metrics = get_clean_data()
    
    # --- SIDEBAR: INTELLIGENT NAVIGATION ---
    st.sidebar.title("🎛️ Controls")
    time_filter = st.sidebar.selectbox(
        "Select Timeframe", 
        ["Week", "Month", "3 Months", "6 Months", "12 Months", "All Time"]
    )
    
    # Logic for Date Filtering
    end_date = full_df['DATE'].max()
    if time_filter == "Week": start_date = end_date - timedelta(days=7)
    elif time_filter == "Month": start_date = end_date - timedelta(days=30)
    elif time_filter == "3 Months": start_date = end_date - timedelta(days=90)
    elif time_filter == "6 Months": start_date = end_date - timedelta(days=180)
    elif time_filter == "12 Months": start_date = end_date - timedelta(days=365)
    else: start_date = full_df['DATE'].min()

    df = full_df[(full_df['DATE'] >= start_date) & (full_df['DATE'] <= end_date)]

    # --- TOP SECTION: KPI HUD ---
    latest = full_df.dropna(subset=[metrics['Weight']]).iloc[-1]
    st.title("⚡ PERFORMANCE COMMAND CENTRE")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Current Weight", f"{latest[metrics['Weight']]} kg")
    c2.metric("Daily Steps", f"{int(latest[metrics['Steps']]):,}")
    c3.metric("Energy Status", f"{latest[metrics['Energy']]}/10")
    c4.metric("Sleep Marker", f"{latest[metrics['Sleep']]}")

    st.divider()

    # --- MAIN VIEW: ISOLATED METRICS ---
    tab1, tab2, tab3 = st.tabs(["📉 Body Composition", "🏃 Activity & Cardio", "😴 Biofeedback"])

    with tab1:
        render_chart(df, metrics['Weight'], "Bodyweight Trend", "#00ffcc", time_filter)
        
    with tab2:
        render_chart(df, metrics['Steps'], "Step Activity", "#FF4B4B", time_filter)
        
    with tab3:
        e_col, s_col = st.columns(2)
        with e_col: render_chart(df, metrics['Energy'], "Energy Levels", "#FFEB3B", time_filter)
        with s_col: render_chart(df, metrics['Stress'], "Stress Markers", "#FF9800", time_filter)

    # --- PT LOG ---
    st.divider()
    with st.expander("📝 Latest Daily Comments"):
        notes = df.dropna(subset=['DAILY COMMENTS']).tail(5)
        for _, row in notes.iterrows():
            st.info(f"**{row['DATE'].strftime('%d %b')}:** {row['DAILY COMMENTS']}")

except Exception as e:
    st.error(f"Intelligence Module Offline: {e}")

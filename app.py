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
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRcgV5PFrp4XmAcNn3cutN0PvxKoZGhTY8wc8NKp70wDdajdsrYPOfNWezEBCoX-wSJyGtHSDDMyqse/pub?output=csv"

@st.cache_data(ttl=60)
def load_and_clean():
    # Load Daily Tracker (Skip spreadsheet headers)
    df = pd.read_csv(CSV_URL, skiprows=4)
    df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
    
    # Convert DATE and PURGE FUTURE ROWS
    df['DATE'] = pd.to_datetime(df['DATE'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['DATE'])
    
    # This line kills the 'child scribble' by ignoring future dates
    df = df[df['DATE'] <= datetime.now()]
    
    # Clean numeric columns
    metrics = ['BODYWEIGHT (kg)', 'STEPS', 'ENERGY LEVELS Scale 1-10', 'STRESS LEVELS Scale 1-10']
    for col in metrics:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
    return df

def render_expert_chart(df, col, title, color, timeframe, is_bar=False):
    plot_df = df.dropna(subset=[col])
    if plot_df.empty: return
    
    fig = go.Figure()
    if is_bar:
        fig.add_trace(go.Bar(x=plot_df['DATE'], y=plot_df[col], marker_color=color, opacity=0.8))
    else:
        fig.add_trace(go.Scatter(x=plot_df['DATE'], y=plot_df[col], 
                                 line=dict(color=color, width=4, shape='spline'),
                                 mode='lines+markers', marker=dict(size=8)))
    
    fig.update_layout(
        template="plotly_dark", title=f"<b>{title}</b> ({timeframe})",
        height=400, margin=dict(l=10, r=10, t=50, b=10),
        hovermode="x unified", showlegend=False,
        xaxis=dict(showgrid=False), yaxis=dict(gridcolor='rgba(255,255,255,0.05)')
    )
    st.plotly_chart(fig, use_container_width=True)

try:
    full_df = load_and_clean()
    
    # --- SIDEBAR: TIME CONTROLS ---
    st.sidebar.title("📈 Time Controls")
    time_choice = st.sidebar.selectbox(
        "Select Visual Window", 
        ["Week", "Month", "3 Months", "6 Months", "12 Months", "All Time"]
    )
    
    # Logic for timeframes
    latest_date = full_df['DATE'].max()
    windows = {"Week": 7, "Month": 30, "3 Months": 90, "6 Months": 180, "12 Months": 365, "All Time": 9999}
    start_date = latest_date - timedelta(days=windows[time_choice])
    df_view = full_df[full_df['DATE'] >= start_date]

    # --- TOP ROW: HUD ---
    st.title("⚡ PERFORMANCE COMMAND CENTRE")
    latest = full_df.dropna(subset=['BODYWEIGHT (kg)']).iloc[-1]
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Bodyweight", f"{latest['BODYWEIGHT (kg)']} kg")
    
    steps = int(latest['STEPS']) if not pd.isna(latest['STEPS']) else 0
    c2.metric("Latest Steps", f"{steps:,}", f"{steps - 12500} vs Goal")
    c3.metric("Energy", f"{latest['ENERGY LEVELS Scale 1-10']}/10")
    c4.metric("Stress", f"{latest['STRESS LEVELS Scale 1-10']}/10")

    st.divider()

    # --- THE DATA TABS ---
    tab_weight, tab_activity, tab_bio = st.tabs(["📉 Composition", "🏃 Activity", "😴 Biofeedback"])

    with tab_weight:
        render_expert_chart(df_view, 'BODYWEIGHT (kg)', "Weight Trend", "#00ffcc", time_choice)
        
    with tab_activity:
        render_expert_chart(df_view, 'STEPS', "Step Activity", "#FF4B4B", time_choice, is_bar=True)
        
    with tab_bio:
        col_e, col_s = st.columns(2)
        with col_e: render_expert_chart(df_view, 'ENERGY LEVELS Scale 1-10', "Energy", "#FFEB3B", time_choice)
        with col_s: render_expert_chart(df_view, 'STRESS LEVELS Scale 1-10', "Stress", "#FF9800", time_choice)

except Exception as e:
    st.error(f"Waiting for Data Sync... Error: {e}")

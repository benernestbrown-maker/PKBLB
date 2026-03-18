import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. UI Configuration
st.set_page_config(page_title="Performance Intelligence Hub", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { color: #00ffcc; font-size: 2.2rem; font-weight: 800; }
    .stPlotlyChart { border: 1px solid #30363d; border-radius: 12px; background-color: #161b22; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Expert Data Engine
# Using the 'Entire Document' link to pull from different GIDs
BASE_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRcgV5PFrp4XmAcNn3cutN0PvxKoZGhTY8wc8NKp70wDdajdsrYPOfNWezEBCoX-wSJyGtHSDDMyqse/pub?"

@st.cache_data(ttl=60)
def fetch_and_clean(gid, skip_rows=0):
    url = f"{BASE_URL}gid={gid}&single=true&output=csv"
    df = pd.read_csv(url, skiprows=skip_rows)
    df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
    
    # Handle Date Parsing
    date_col = 'DATE' if 'DATE' in df.columns else 'day'
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
        df = df.dropna(subset=[date_col])
        # Crucial: Purge future-dated placeholder rows
        df = df[df[date_col] <= datetime.now()]
    return df, date_col

def plot_metric(df, date_col, y_col, title, color, timeframe, is_bar=False):
    plot_df = df.dropna(subset=[y_col])
    if plot_df.empty: return
    
    fig = go.Figure()
    if is_bar:
        fig.add_trace(go.Bar(x=plot_df[date_col], y=plot_df[y_col], marker_color=color, opacity=0.8))
    else:
        fig.add_trace(go.Scatter(x=plot_df[date_col], y=plot_df[y_col], 
                                 line=dict(color=color, width=4, shape='spline'),
                                 mode='lines+markers', marker=dict(size=8)))
    
    fig.update_layout(
        template="plotly_dark", title=f"<b>{title}</b> ({timeframe})",
        height=380, margin=dict(l=10, r=10, t=50, b=10),
        hovermode="x unified", showlegend=False,
        xaxis=dict(showgrid=False), yaxis=dict(gridcolor='rgba(255,255,255,0.05)')
    )
    st.plotly_chart(fig, use_container_width=True)

# --- EXECUTION ---
try:
    # 3. Load Datasets (GIDs for Daily Tracker and InBody Metrics)
    tracker_df, t_date = fetch_and_clean(gid="0", skip_rows=4)
    inbody_df, i_date = fetch_and_clean(gid="1795026937", skip_rows=2) # Example GID for InBody tab
    
    # 4. Global Sidebar Filters
    st.sidebar.title("📈 Intelligence Controls")
    time_choice = st.sidebar.selectbox(
        "Select Visual Window", 
        ["Week", "Month", "3 Months", "6 Months", "12 Months", "All Time"]
    )
    
    # Timeframe Logic
    latest_date = tracker_df[t_date].max()
    windows = {"Week": 7, "Month": 30, "3 Months": 90, "6 Months": 180, "12 Months": 365, "All Time": 9999}
    start_date = latest_date - timedelta(days=windows[time_choice])
    
    df_view = tracker_df[tracker_df[t_date] >= start_date]
    ib_view = inbody_df[inbody_df[i_date] >= start_date]

    st.title("⚡ PERFORMANCE COMMAND CENTRE")
    
    # 5. Dashboard Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📉 Composition", "🏃 Activity", "😴 Biofeedback"])

    with tab1:
        # High-level Metrics Row
        latest = tracker_df.iloc[-1]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Weight", f"{latest['BODYWEIGHT (kg)']}kg")
        c2.metric("Steps", f"{int(latest['STEPS']):,}")
        c3.metric("Energy", f"{latest['ENERGY LEVELS Scale 1-10']}/10")
        c4.metric("Sleep Quality", f"{latest['SLEEP QUALITY Sleep Score OR Scale 1-10']}")
        
        st.divider()
        plot_metric(df_view, t_date, 'BODYWEIGHT (kg)', "Weight Snapshot", "#00ffcc", time_choice)

    with tab2:
        st.subheader("InBody & Physical Trends")
        # Body Fat % and Muscle Mass from the InBody tab
        col_bf, col_mm = st.columns(2)
        with col_bf: plot_metric(ib_view, i_date, 'BF%', "Body Fat %", "#FF4B4B", time_choice)
        with col_mm: plot_metric(ib_view, i_date, 'MUSCLE MASS', "Muscle Mass (kg)", "#00FFAA", time_choice)

    with tab3:
        plot_metric(df_view, t_date, 'STEPS', "Step Volume", "#00ffcc", time_choice, is_bar=True)

    with tab4:
        col_en, col_st = st.columns(2)
        with col_en: plot_metric(df_view, t_date, 'ENERGY LEVELS Scale 1-10', "Energy", "#FFEB3B", time_choice)
        with col_st: plot_metric(df_view, t_date, 'STRESS LEVELS Scale 1-10', "Stress", "#FF9800", time_choice)

except Exception as e:
    st.error(f"Waiting for Data Sync: {e}")
    

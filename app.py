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

# GIDs
TRACKER_GID = "0"
OURA_GID = "502032885"
INBODY_GID = "686934394" 

BASE_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRcgV5PFrp4XmAcNn3cutN0PvxKoZGhTY8wc8NKp70wDdajdsrYPOfNWezEBCoX-wSJyGtHSDDMyqse/pub?"

@st.cache_data(ttl=60)
def fetch_all_data():
    def get_df(gid, skip=0):
        url = f"{BASE_URL}gid={gid}&single=true&output=csv"
        try:
            df = pd.read_csv(url, skiprows=skip)
            df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
            return df
        except: return pd.DataFrame()

    # Tracker
    df = get_df(TRACKER_GID, skip=4)
    t_date = next((c for c in df.columns if 'DATE' in c.upper()), None)
    if t_date and not df.empty:
        df[t_date] = pd.to_datetime(df[t_date], dayfirst=True, errors='coerce')
        df = df.dropna(subset=[t_date])
        df = df[df[t_date] <= datetime.now()]
    
    for col in ['BODYWEIGHT (kg)', 'STEPS']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
    
    # Oura - Pulling Decisive Recovery Metrics
    oura = get_df(OURA_GID)
    o_date = None
    if not oura.empty:
        o_date = next((c for c in oura.columns if 'DAY' in c.upper() or 'DATE' in c.upper()), oura.columns[0])
        oura[o_date] = pd.to_datetime(oura[o_date], errors='coerce')
        oura = oura.dropna(subset=[o_date])
        oura = oura[oura[o_date] <= datetime.now()]
        # Clean Oura Numeric
        oura_cols = ['readiness_score', 'score_sleep', 'average_hrv', 'rest_heart_rate', 'respiratory_rate']
        for c in oura_cols:
            if c in oura.columns:
                oura[c] = pd.to_numeric(oura[c], errors='coerce')

    # InBody
    inbody = get_df(INBODY_GID, skip=2)
    i_date = None
    if not inbody.empty:
        i_date = next((c for c in inbody.columns if 'DATE' in c.upper()), inbody.columns[0])
        inbody[i_date] = pd.to_datetime(inbody[i_date], dayfirst=True, errors='coerce')
        inbody = inbody.dropna(subset=[i_date])
        inbody = inbody[inbody[i_date] <= datetime.now()]

    return df, oura, inbody, t_date, o_date, i_date

def build_combined_chart(data, x_col, y_cols, title, timeframe):
    """Amalgamates multiple metrics into one clear visual"""
    fig = go.Figure()
    colors = ['#00ffcc', '#FF4B4B', '#9C27B0', '#FFEB3B', '#00FFAA']
    
    for i, col in enumerate(y_cols):
        if col in data.columns:
            clean = data.dropna(subset=[col])
            fig.add_trace(go.Scatter(
                x=clean[x_col], y=clean[col], 
                name=col.replace('_', ' ').title(),
                line=dict(color=colors[i % len(colors)], width=3, shape='spline'),
                mode='lines+markers'
            ))
            
    fig.update_layout(
        template="plotly_dark", title=f"<b>{title}</b>",
        height=450, margin=dict(l=10, r=10, t=50, b=10),
        hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

try:
    df, oura, inbody, t_date, o_date, i_date = fetch_all_data()
    
    # --- CONTROLS ---
    st.sidebar.title("🎛️ Performance Controls")
    time_choice = st.sidebar.selectbox("Analysis Window", ["Week", "Month", "3 Months", "6 Months", "All Time"])
    windows = {"Week": 7, "Month": 30, "3 Months": 90, "6 Months": 180, "All Time": 9999}
    
    start_date = df[t_date].max() - timedelta(days=windows[time_choice])
    df_v = df[df[t_date] >= start_date]
    ou_v = oura[oura[o_date] >= start_date] if not oura.empty else pd.DataFrame()
    ib_v = inbody[inbody[i_date] >= start_date] if not inbody.empty else pd.DataFrame()

    st.title("⚡ BEN'S PERFORMANCE COMMAND CENTRE")

    # --- TABS ---
    t1, t2, t3, t4 = st.tabs(["📊 Vitals Overview", "📉 Composition Hub", "😴 Oura Deep-Dive", "📅 Intelligence Timeline"])

    with t1:
        c1, c2, c3, c4 = st.columns(4)
        latest_w = df.dropna(subset=['BODYWEIGHT (kg)']).iloc[-1]
        c1.metric("Weight", f"{latest_w['BODYWEIGHT (kg)']} kg")
        s_val = int(latest_w['STEPS']) if not pd.isna(latest_w['STEPS']) else 0
        c2.metric("Steps", f"{s_val:,}")
        
        if not ou_v.empty:
            lo = ou_v.iloc[-1]
            c3.metric("HRV", f"{int(lo['average_hrv'])}ms")
            c4.metric("Readiness", f"{int(lo['readiness_score'])}")
        
        st.subheader("Amalgamated Weight & Activity Trend")
        # Dual Axis for Weight vs Steps
        fig_dual = go.Figure()
        fig_dual.add_trace(go.Scatter(x=df_v[t_date], y=df_v['BODYWEIGHT (kg)'], name="Weight", line=dict(color='#00ffcc', width=4)))
        fig_dual.add_trace(go.Bar(x=df_v[t_date], y=df_v['STEPS'], name="Steps", marker_color='rgba(255, 75, 75, 0.3)', yaxis='y2'))
        fig_dual.update_layout(
            template="plotly_dark", yaxis2=dict(overlaying='y', side='right', showgrid=False),
            legend=dict(orientation="h"), height=400
        )
        st.plotly_chart(fig_dual, use_container_width=True)

    with t2:
        st.subheader("Master Composition Analysis")
        # Combined InBody Metrics
        if not ib_v.empty:
            bf_col = next((c for c in ib_v.columns if 'BF%' in c or 'FAT' in c.upper()), 'BF%')
            mm_col = next((c for c in ib_v.columns if 'MUSCLE' in c.upper()), 'MUSCLE MASS')
            build_combined_chart(ib_v, i_date, [bf_col, mm_col], "Body Fat % vs Muscle Mass Trend", time_choice)
        else:
            st.info("Syncing InBody data...")

    with t3:
        st.subheader("Master Recovery Intelligence")
        if not ou_v.empty:
            # Amalgamated Oura Chart
            build_combined_chart(ou_v, o_date, ['readiness_score', 'score_sleep', 'average_hrv'], "Combined Readiness, Sleep & HRV", time_choice)
            
            st.divider()
            col_a, col_b = st.columns(2)
            with col_a:
                # Resting Heart Rate (Decisive)
                fig_rhr = go.Figure(go.Scatter(x=ou_v[o_date], y=ou_v['rest_heart_rate'], name="RHR", line=dict(color='#FF4B4B', shape='spline')))
                fig_rhr.update_layout(template="plotly_dark", title="Resting Heart Rate (Lower is better)", height=300)
                st.plotly_chart(fig_rhr, use_container_width=True)
            with col_b:
                # Respiratory Rate (Decisive for illness/fatigue)
                fig_rr = go.Figure(go.Scatter(x=ou_v[o_date], y=ou_v['respiratory_rate'], name="Resp Rate", line=dict(color='#00FFAA', shape='spline')))
                fig_rr.update_layout(template="plotly_dark", title="Respiratory Rate (Stability check)", height=300)
                st.plotly_chart(fig_rr, use_container_width=True)

    with t4:
        st.subheader("Master Performance Correlation")
        # All decisive data points
        if not ou_v.empty:
            # Merge Oura and Tracker for a single 'Correlation' chart
            merged = pd.merge(df_v[[t_date, 'STEPS', 'BODYWEIGHT (kg)']], 
                              ou_v[[o_date, 'readiness_score', 'average_hrv']], 
                              left_on=t_date, right_on=o_date, how='inner')
            
            build_combined_chart(merged, t_date, ['STEPS', 'average_hrv', 'readiness_score'], "Activity vs Biological Recovery", time_choice)
        
        st.divider()
        st.write("📈 **Expert Note:** Use this tab to see if higher step days are causing a drop in HRV/Readiness 24-48 hours later.")

except Exception as e:
    st.error(f"Syncing... Ensure column names match and GIDs are current. Error: {e}")

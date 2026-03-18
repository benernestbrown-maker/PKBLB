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

# GIDs - UPDATE THESE IF DATA IS MISSING
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
    df['DATE'] = pd.to_datetime(df['DATE'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['DATE'])
    df = df[df['DATE'] <= datetime.now()]
    for col in ['BODYWEIGHT (kg)', 'STEPS']:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
    
    # Oura
    oura = get_df(OURA_GID)
    if not oura.empty:
        oura['day'] = pd.to_datetime(oura['day'], errors='coerce')
        oura = oura[oura['day'] <= datetime.now()]

    # InBody
    inbody = get_df(INBODY_GID, skip=2)
    if not inbody.empty:
        # Assuming InBody tab has a 'DATE' or 'Date' column
        d_col = 'DATE' if 'DATE' in inbody.columns else inbody.columns[0]
        inbody[d_col] = pd.to_datetime(inbody[d_col], dayfirst=True, errors='coerce')
        inbody = inbody.dropna(subset=[d_col])

    return df, oura, inbody

def build_chart(df, x_col, y_col, title, color, timeframe, is_bar=False, show_avg=False):
    data = df.dropna(subset=[y_col]).copy()
    if data.empty: return
    
    fig = go.Figure()
    if is_bar:
        fig.add_trace(go.Bar(x=data[x_col], y=data[y_col], marker_color=color, opacity=0.8))
    else:
        fig.add_trace(go.Scatter(x=data[x_col], y=data[y_col], name="Daily",
                                 line=dict(color=color, width=2), mode='lines+markers'))
        if show_avg and len(data) > 7:
            data['avg'] = data[y_col].rolling(window=7).mean()
            fig.add_trace(go.Scatter(x=data[x_col], y=data['avg'], name="7-Day Avg",
                                     line=dict(color='white', width=4, dash='dot')))
    
    fig.update_layout(template="plotly_dark", title=f"<b>{title}</b>", height=380, 
                      margin=dict(l=10, r=10, t=50, b=10), hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

try:
    df, oura, inbody = fetch_all_data()
    
    # --- TIME CONTROLS ---
    time_choice = st.sidebar.selectbox("Window", ["Week", "Month", "3 Months", "6 Months", "All Time"])
    windows = {"Week": 7, "Month": 30, "3 Months": 90, "6 Months": 180, "All Time": 9999}
    start_date = df['DATE'].max() - timedelta(days=windows[time_choice])
    
    df_v = df[df['DATE'] >= start_date]
    ou_v = oura[oura['day'] >= start_date] if not oura.empty else pd.DataFrame()
    ib_v = inbody[inbody.iloc[:,0] >= start_date] if not inbody.empty else pd.DataFrame()

    st.title("⚡ PERFORMANCE COMMAND CENTRE")

    # --- TABS ---
    t1, t2, t3, t4 = st.tabs(["📊 Vitals", "📉 Composition", "😴 Recovery", "📅 Timeline"])

    with t1:
        lw = df.dropna(subset=['BODYWEIGHT (kg)']).iloc[-1]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Weight", f"{lw['BODYWEIGHT (kg)']} kg")
        s_val = int(lw['STEPS']) if not pd.isna(lw['STEPS']) else 0
        c2.metric("Steps", f"{s_val:,}", f"{s_val - 12500}")
        if not ou_v.empty:
            lo = ou_v.iloc[-1]
            c3.metric("Readiness", int(lo['readiness_score']))
            c4.metric("Sleep", int(lo['score_sleep']))
        
        build_chart(df_v, 'DATE', 'BODYWEIGHT (kg)', "Weight Trend", "#00ffcc", time_choice, show_avg=True)

    with t2:
        st.subheader("InBody Decisive Data")
        if not ib_v.empty:
            # Update 'BF%' and 'MUSCLE MASS' to match your actual InBody column names
            col_a, col_b = st.columns(2)
            with col_a: build_chart(ib_v, ib_v.columns[0], 'BF%', "Body Fat %", "#FF4B4B", time_choice)
            with col_b: build_chart(ib_v, ib_v.columns[0], 'MUSCLE MASS', "Muscle Mass (kg)", "#00FFAA", time_choice)
        else:
            st.info("Check InBody GID to enable Body Fat % and Muscle Mass tracking.")

    with t3:
        if not ou_v.empty:
            build_chart(ou_v, 'day', 'average_hrv', "HRV (ms)", "#00ffcc", time_choice)
            build_chart(ou_v, 'score_sleep', "Sleep Score", "#9C27B0", time_choice)
        else: st.warning("Oura data missing.")

    with t4:
        st.subheader("Master Timeline")
        build_chart(df_v, 'DATE', 'STEPS', "Steps", "#FF4B4B", time_choice, is_bar=True)
        if not ou_v.empty:
            build_chart(ou_v, 'day', 'average_hrv', "Recovery (HRV)", "#00ffcc", time_choice)
        build_chart(df_v, 'DATE', 'BODYWEIGHT (kg)', "Weight (kg)", "#00ffcc", time_choice)

except Exception as e:
    st.error(f"Syncing... If this persists, check your tab GIDs. Error: {e}")

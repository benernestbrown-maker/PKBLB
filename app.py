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

# GIDs - Verified by User
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

    # Tracker Cleaning (Row 5 start)
    df = get_df(TRACKER_GID, skip=4)
    t_date = next((c for c in df.columns if 'DATE' in c.upper()), None)
    if t_date and not df.empty:
        df[t_date] = pd.to_datetime(df[t_date], dayfirst=True, errors='coerce')
        df = df.dropna(subset=[t_date])
        df = df[df[t_date] <= datetime.now()]
    
    for col in ['BODYWEIGHT (kg)', 'STEPS']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
    
    # Oura Cleaning
    oura = get_df(OURA_GID)
    o_date = None
    if not oura.empty:
        o_date = next((c for c in oura.columns if 'DAY' in c.upper() or 'DATE' in c.upper()), oura.columns[0])
        oura[o_date] = pd.to_datetime(oura[o_date], errors='coerce')
        oura = oura.dropna(subset=[o_date])
        oura = oura[oura[o_date] <= datetime.now()]

    # InBody Cleaning (Row 3 Headers)
    inbody = get_df(INBODY_GID, skip=2)
    i_date = None
    if not inbody.empty:
        i_date = next((c for c in inbody.columns if 'DATE' in c.upper()), inbody.columns[0])
        inbody[i_date] = pd.to_datetime(inbody[i_date], dayfirst=True, errors='coerce')
        inbody = inbody.dropna(subset=[i_date])
        inbody = inbody[inbody[i_date] <= datetime.now()]

    return df, oura, inbody, t_date, o_date, i_date

def build_chart(df, x_col, y_col, title, color, is_bar=False, show_avg=False):
    if y_col not in df.columns: return 
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
    df, oura, inbody, t_date, o_date, i_date = fetch_all_data()
    
    if df.empty:
        st.warning("Still waiting for data from the Google Sheet...")
        st.stop()

    # --- CONTROLS ---
    st.sidebar.title("🎛️ Controls")
    time_choice = st.sidebar.selectbox("Window", ["Week", "Month", "3 Months", "6 Months", "All Time"])
    windows = {"Week": 7, "Month": 30, "3 Months": 90, "6 Months": 180, "All Time": 9999}
    
    latest_val = df[t_date].max()
    start_date = latest_val - timedelta(days=windows[time_choice])
    
    df_v = df[df[t_date] >= start_date]
    ou_v = oura[oura[o_date] >= start_date] if not oura.empty else pd.DataFrame()
    ib_v = inbody[inbody[i_date] >= start_date] if not inbody.empty else pd.DataFrame()

    st.title("⚡ PERFORMANCE COMMAND CENTRE")

    # --- TABS ---
    t1, t2, t3, t4 = st.tabs(["📊 Vitals", "📉 Composition", "😴 Recovery", "📅 Timeline"])

    with t1:
        weight_data = df.dropna(subset=['BODYWEIGHT (kg)'])
        latest_w = weight_data.iloc[-1] if not weight_data.empty else None
        
        c1, c2, c3, c4 = st.columns(4)
        if latest_w is not None:
            c1.metric("Weight", f"{latest_w['BODYWEIGHT (kg)']} kg")
            step_val = int(latest_w['STEPS']) if not pd.isna(latest_w['STEPS']) else 0
            c2.metric("Steps", f"{step_val:,}", f"{step_val - 12500}")
        
        if not ou_v.empty:
            read_col = next((c for c in ou_v.columns if 'READINESS' in c.upper()), None)
            slp_score = next((c for c in ou_v.columns if 'SLEEP' in c.upper() and 'SCORE' in c.upper()), None)
            
            if read_col:
                lo_r = ou_v.dropna(subset=[read_col]).iloc[-1]
                c3.metric("Readiness", f"{int(lo_r[read_col])}")
            if slp_score:
                lo_s = ou_v.dropna(subset=[slp_score]).iloc[-1]
                c4.metric("Sleep", f"{int(lo_s[slp_score])}")
        
        build_chart(df_v, t_date, 'BODYWEIGHT (kg)', "Weight Trend", "#00ffcc", show_avg=True)

    with t2:
        st.subheader("InBody Decisive Data")
        if not ib_v.empty:
            col_a, col_b = st.columns(2)
            bf_col = next((c for c in ib_v.columns if 'BF%' in c or 'FAT' in c.upper()), None)
            mm_col = next((c for c in ib_v.columns if 'MUSCLE' in c.upper()), None)
            
            if bf_col:
                with col_a: build_chart(ib_v, i_date, bf_col, "Body Fat %", "#FF4B4B")
            if mm_col:
                with col_b: build_chart(ib_v, i_date, mm_col, "Muscle Mass (kg)", "#00FFAA")
        else:
            st.info("No InBody data found. Confirm your InBody GID is correct.")

    with t3:
        if not ou_v.empty:
            hrv_col = next((c for c in ou_v.columns if 'HRV' in c.upper()), None)
            slp_col = next((c for c in ou_v.columns if 'SLEEP' in c.upper() and 'SCORE' in c.upper()), None)
            if hrv_col: build_chart(ou_v, o_date, hrv_col, "HRV (ms)", "#00ffcc")
            if slp_col: build_chart(ou_v, o_date, slp_col, "Sleep Score", "#9C27B0")
        else: st.warning("Oura data missing.")

    with t4:
        st.subheader("Master Performance Timeline")
        build_chart(df_v, t_date, 'STEPS', "Steps", "#FF4B4B", is_bar=True)
        if not ou_v.empty:
            hrv_tl = next((c for c in ou_v.columns if 'HRV' in c.upper()), None)
            if hrv_tl: build_chart(ou_v, o_date, hrv_tl, "Recovery (HRV)", "#00ffcc")
        build_chart(df_v, t_date, 'BODYWEIGHT (kg)', "Weight (kg)", "#00ffcc", show_avg=True)

except Exception as e:
    st.error(f"Syncing... Error: {e}")

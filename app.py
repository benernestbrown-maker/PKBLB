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
            # Expert cleaning of headers
            df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
            return df
        except: return pd.DataFrame()

    # --- TRACKER CLEANING (Skip 4 rows: Data row 5) ---
    df = get_df(TRACKER_GID, skip=4)
    date_col = next((c for c in df.columns if 'DATE' in c.upper()), None)
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
        df = df.dropna(subset=[date_col])
        df = df[df[date_col] <= datetime.now()]
    
    for col in ['BODYWEIGHT (kg)', 'STEPS']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
    
    # --- OURA CLEANING ---
    oura = get_df(OURA_GID)
    if not oura.empty:
        o_date = next((c for c in oura.columns if 'DAY' in c.upper() or 'DATE' in c.upper()), oura.columns[0])
        oura[o_date] = pd.to_datetime(oura[o_date], errors='coerce')
        oura = oura.dropna(subset=[o_date])
        oura = oura[oura[o_date] <= datetime.now()]

    # --- INBODY CLEANING (Skip 2 rows: Headers on row 3) ---
    inbody = get_df(INBODY_GID, skip=2)
    i_date = None
    if not inbody.empty:
        i_date = next((c for c in inbody.columns if 'DATE' in c.upper()), inbody.columns[0])
        inbody[i_date] = pd.to_datetime(inbody[i_date], dayfirst=True, errors='coerce')
        inbody = inbody.dropna(subset=[i_date])
        inbody = inbody[inbody[i_date] <= datetime.now()]

    return df, oura, inbody, date_col, i_date

def build_chart(df, x_col, y_col, title, color, timeframe, is_bar=False, show_avg=False):
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
    df, oura, inbody, t_date_name, i_date_name = fetch_all_data()
    
    # --- TIME CONTROLS ---
    st.sidebar.title("🎛️ Dashboard Controls")
    time_choice = st.sidebar.selectbox("Window", ["Week", "Month", "3 Months", "6 Months", "All Time"])
    windows = {"Week": 7, "Month": 30, "3 Months": 90, "6 Months": 180, "All Time": 9999}
    
    latest_data_date = df[t_date_name].max()
    start_date = latest_data_date - timedelta(days=windows[time_choice])
    
    df_v = df[df[t_date_name] >= start_date]
    ou_v = oura[oura.iloc[:,0] >= start_date] if not oura.empty else pd.DataFrame()
    ib_v = inbody[inbody[i_date_name] >= start_date] if not inbody.empty else pd.DataFrame()

    st.title("⚡ PERFORMANCE COMMAND CENTRE")

    # --- TABS ---
    t1, t2, t3, t4 = st.tabs(["📊 Vitals", "📉 Composition", "😴 Recovery", "📅 Timeline"])

    with t1:
        latest_weight_row = df.dropna(subset=['BODYWEIGHT (kg)']).iloc[-1]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Weight", f"{latest_weight_row['BODYWEIGHT (kg)']} kg")
        
        step_val = int(latest_weight_row['STEPS']) if not pd.isna(latest_weight_row['STEPS']) else 0
        c2.metric("Steps", f"{step_val:,}", f"{step_val - 12500}")
        
        if not ou_v.empty:
            lo = ou_v.dropna(subset=['readiness_score']).iloc[-1]
            c3.metric("Readiness", f"{int(lo['readiness_score'])}")
            c4.metric("Sleep", f"{int(lo['score_sleep'])}")
        
        build_chart(df_v, t_date_name, 'BODYWEIGHT (kg)', "Weight Trend", "#00ffcc", time_choice, show_avg=True)

    with t2:
        st.subheader("InBody Decisive Data")
        if not ib_v.empty:
            col_a, col_b = st.columns(2)
            bf_col = next((c for c in ib_v.columns if 'BF%' in c or 'FAT' in c.upper()), None)
            mm_col = next((c for c in ib_v.columns if 'MUSCLE' in c.upper()), None)
            
            if bf_col:
                with col_a: build_chart(ib_v, i_date_name, bf_col, "Body Fat %", "#FF4B4B", time_choice)
            if mm_col:
                with col_b: build_chart(ib_v, i_date_name, mm_col, "Muscle Mass (kg)", "#00FFAA", time_choice)
        else:
            st.info("No InBody data found within this timeframe. Ensure headers are on Row 3.")

    with t3:
        if not ou_v.empty:
            build_chart(ou_v, ou_v.columns[0], 'average_hrv', "HRV (ms)", "#00ffcc", time_choice)
            build_chart(ou_v, ou_v.columns[0], 'score_sleep', "Sleep Score", "#9C27B0", time_choice)
        else: st.warning("Oura data missing.")

    with t4:
        st.subheader("Master Performance Timeline")
        build_chart(df_v, t_date_name, 'STEPS', "Steps", "#FF4B4B", time_choice, is_bar=True)
        if not ou_v.empty:
            build_chart(ou_v, ou_v.columns[0], 'average_hrv', "Recovery (HRV)", "#00ffcc", time_choice)
        build_chart(df_v, t_date_name, 'BODYWEIGHT (kg)', "Weight (kg)", "#00ffcc", time_choice, show_avg=True)

except Exception as e:
    st.error(f"Syncing... Error: {e}")

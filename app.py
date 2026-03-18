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
    def get_df_smart(gid):
        url = f"{BASE_URL}gid={gid}&single=true&output=csv"
        try:
            raw_df = pd.read_csv(url, header=None, nrows=10)
            header_row = 0
            for i, row in raw_df.iterrows():
                row_str = " ".join(row.astype(str).values).upper()
                if any(k in row_str for k in ['DATE', 'DAY', 'BF%', 'WEIGHT', 'HRV', 'READINESS']):
                    header_row = i
                    break
            df = pd.read_csv(url, skiprows=header_row)
            df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
            return df
        except: return pd.DataFrame()

    tracker = get_df_smart(TRACKER_GID)
    oura = get_df_smart(OURA_GID)
    inbody = get_df_smart(INBODY_GID)

    # Clean Tracker
    if not tracker.empty:
        t_date = next((c for c in tracker.columns if 'DATE' in c.upper()), tracker.columns[0])
        tracker[t_date] = pd.to_datetime(tracker[t_date], dayfirst=True, errors='coerce')
        tracker = tracker.dropna(subset=[t_date])
        tracker = tracker[tracker[t_date] <= datetime.now()]
        tracker['BODYWEIGHT (kg)'] = pd.to_numeric(tracker.get('BODYWEIGHT (kg)', 0), errors='coerce')
        tracker['STEPS'] = pd.to_numeric(tracker.get('STEPS', 0), errors='coerce')
    else: t_date = None

    # Clean Oura with YOUR exact names
    if not oura.empty:
        o_date = 'day' if 'day' in oura.columns else oura.columns[0]
        oura[o_date] = pd.to_datetime(oura[o_date], errors='coerce')
        oura = oura.dropna(subset=[o_date])
        oura = oura[oura[o_date] <= datetime.now()]
    else: o_date = None

    # Clean InBody
    if not inbody.empty:
        i_date = next((c for c in inbody.columns if 'DATE' in c.upper()), inbody.columns[0])
        inbody[i_date] = pd.to_datetime(inbody[i_date], dayfirst=True, errors='coerce')
        inbody = inbody.dropna(subset=[i_date])
    else: i_date = None

    return tracker, oura, inbody, t_date, o_date, i_date

def build_master_chart(data, x_col, y_cols, title, colors=['#00ffcc', '#FF4B4B', '#9C27B0', '#FFEB3B']):
    fig = go.Figure()
    valid_cols = [c for c in y_cols if c in data.columns]
    if not valid_cols: return
    
    for i, col in enumerate(valid_cols):
        clean = data.dropna(subset=[col])
        fig.add_trace(go.Scatter(x=clean[x_col], y=clean[col], name=col.replace('_', ' ').title(),
                                 line=dict(color=colors[i%len(colors)], width=3, shape='spline')))
    fig.update_layout(template="plotly_dark", title=f"<b>{title}</b>", height=450, 
                      hovermode="x unified", legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)

try:
    df, oura, inbody, t_date, o_date, i_date = fetch_all_data()
    
    st.sidebar.title("🎛️ Hub Controls")
    time_choice = st.sidebar.selectbox("Window", ["Week", "Month", "3 Months", "All Time"])
    windows = {"Week": 7, "Month": 30, "3 Months": 90, "All Time": 9999}
    
    start_date = df[t_date].max() - timedelta(days=windows[time_choice])
    df_v = df[df[t_date] >= start_date]
    ou_v = oura[oura[o_date] >= start_date] if not oura.empty else pd.DataFrame()
    ib_v = inbody[inbody[i_date] >= start_date] if not inbody.empty else pd.DataFrame()

    st.title("⚡ PERFORMANCE COMMAND CENTRE")

    t1, t2, t3, t4 = st.tabs(["📊 Vitals", "📉 Composition", "😴 Oura Deep-Dive", "📅 Master Timeline"])

    with t1:
        c1, c2, c3, c4 = st.columns(4)
        latest_w = df.dropna(subset=['BODYWEIGHT (kg)']).iloc[-1]
        c1.metric("Weight", f"{latest_w['BODYWEIGHT (kg)']} kg")
        s_val = int(latest_w['STEPS']) if not pd.isna(latest_w['STEPS']) else 0
        c2.metric("Steps", f"{s_val:,}", f"{s_val - 12500}")
        if not ou_v.empty:
            lo = ou_v.iloc[-1]
            c3.metric("Readiness", f"{int(lo['readiness_score'])}")
            c4.metric("HRV", f"{int(lo['average_hrv'])}ms")
        
        build_master_chart(df_v, t_date, ['BODYWEIGHT (kg)'], "Amalgamated Weight Progress")

    with t2:
        st.subheader("Master Composition Amalgamation")
        if not ib_v.empty:
            bf = next((c for c in ib_v.columns if 'BF%' in c or 'FAT' in c.upper()), None)
            mm = next((c for c in ib_v.columns if 'MUSCLE' in c.upper()), None)
            build_master_chart(ib_v, i_date, [c for c in [bf, mm] if c], "Combined Physical Trends")
        else: st.info("InBody Data Syncing...")

    with t3:
        st.subheader("Master Recovery Amalgamation")
        if not ou_v.empty:
            # All DECISIVE metrics in one master graph
            build_master_chart(ou_v, o_date, ['readiness_score', 'sleep_score', 'average_hrv'], "Readiness vs Sleep vs HRV")
            
            st.divider()
            col_a, col_b = st.columns(2)
            with col_a:
                build_master_chart(ou_v, o_date, ['lowest_heart_rate'], "Lowest Heart Rate (Nightly)", ['#FF4B4B'])
            with col_b:
                build_master_chart(ou_v, o_date, ['temperature_deviation'], "Temp Deviation", ['#9C27B0'])
        else: st.warning("Oura data not found.")

    with t4:
        st.subheader("The Master Correlation Timeline")
        # Activity vs Recovery
        fig_master = go.Figure()
        fig_master.add_trace(go.Bar(x=df_v[t_date], y=df_v['STEPS'], name="Steps", marker_color='rgba(0, 255, 204, 0.2)'))
        if not ou_v.empty:
            fig_master.add_trace(go.Scatter(x=ou_v[o_date], y=ou_v['readiness_score'], name="Readiness", line=dict(color='#FF4B4B', width=4)))
        fig_master.update_layout(template="plotly_dark", title="Daily Activity vs. Next-Day Readiness", height=500)
        st.plotly_chart(fig_master, use_container_width=True)

except Exception as e:
    st.error(f"Intelligence Module Error: {e}")

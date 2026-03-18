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
    def get_df_smart(gid, skip_val=0):
        url = f"{BASE_URL}gid={gid}&single=true&output=csv"
        try:
            df = pd.read_csv(url, skiprows=skip_val)
            df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
            return df
        except: return pd.DataFrame()

    # --- TRACKER CLEANING (Column S specific) ---
    df = get_df_smart(TRACKER_GID, 4)
    t_date = next((c for c in df.columns if 'DATE' in c.upper()), None)
    
    if t_date and not df.empty:
        df[t_date] = pd.to_datetime(df[t_date], dayfirst=True, errors='coerce')
        df = df.dropna(subset=[t_date])
        df = df[df[t_date] <= datetime.now()]
        
        # Clean Bodyweight
        df['BODYWEIGHT (kg)'] = pd.to_numeric(df.get('BODYWEIGHT (kg)', 0), errors='coerce')
        
        # Clean STEPS (Column S) - The "Dirty Data" Fix
        # 1. Find the column (S is usually index 18)
        step_col = next((c for c in df.columns if 'STEPS' in c.upper()), df.columns[18] if len(df.columns) > 18 else None)
        if step_col:
            # Remove repeating "STEPS" text and commas
            df[step_col] = df[step_col].astype(str).str.replace('STEPS', '', case=False)
            df[step_col] = df[step_col].str.replace(',', '')
            df['STEPS_CLEAN'] = pd.to_numeric(df[step_col], errors='coerce')

    # --- OURA CLEANING ---
    oura = get_df_smart(OURA_GID, 0)
    o_date = None
    if not oura.empty:
        o_date = next((c for c in oura.columns if 'DAY' in c.lower()), oura.columns[0])
        oura[o_date] = pd.to_datetime(oura[o_date], errors='coerce')
        oura = oura.dropna(subset=[o_date])

    # --- INBODY CLEANING ---
    inbody = get_df_smart(INBODY_GID, 2)
    i_date = None
    if not inbody.empty:
        i_date = next((c for c in inbody.columns if 'DATE' in c.upper()), inbody.columns[0])
        inbody[i_date] = pd.to_datetime(inbody[i_date], dayfirst=True, errors='coerce')

    return df, oura, inbody, t_date, o_date, i_date

def build_master_chart(data, x_col, y_cols, title, colors=['#00ffcc', '#FF4B4B', '#9C27B0']):
    fig = go.Figure()
    actual_cols = [c for c in y_cols if c in data.columns]
    if not actual_cols: return
    
    for i, col in enumerate(actual_cols):
        clean = data.dropna(subset=[col])
        fig.add_trace(go.Scatter(x=clean[x_col], y=clean[col], name=col.replace('_CLEAN','').title(),
                                 line=dict(color=colors[i%len(colors)], width=3, shape='spline'),
                                 mode='lines+markers'))
    
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

    st.title("⚡ BEN'S PERFORMANCE HUB")

    tabs = st.tabs(["📊 Vitals", "📉 Composition", "😴 Oura Recovery", "📅 Timeline"])

    with tabs[0]:
        latest = df.dropna(subset=['BODYWEIGHT (kg)']).iloc[-1]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Weight", f"{latest['BODYWEIGHT (kg)']} kg")
        s_val = int(latest['STEPS_CLEAN']) if not pd.isna(latest['STEPS_CLEAN']) else 0
        c2.metric("Steps", f"{s_val:,}", f"{s_val - 12500}")
        
        if not ou_v.empty:
            lo = ou_v.iloc[-1]
            hrv_k = next((c for c in ou_v.columns if 'hrv' in c.lower()), None)
            if hrv_k: c3.metric("HRV", f"{int(lo[hrv_k])}ms")
            readi_k = next((c for c in ou_v.columns if 'readiness' in c.lower()), None)
            if readi_k: c4.metric("Readiness", f"{int(lo[readi_k])}")

        build_master_chart(df_v, t_date, ['BODYWEIGHT (kg)'], "Amalgamated Weight Trend")

    with tabs[1]:
        st.subheader("InBody Composition Analysis")
        if not ib_v.empty:
            bf = next((c for c in ib_v.columns if 'BF%' in c or 'FAT' in c.upper()), None)
            mm = next((c for c in ib_v.columns if 'MUSCLE' in c.upper()), None)
            build_master_chart(ib_v, i_date, [c for c in [bf, mm] if c], "Fat % vs Muscle Mass")
        else: st.info("Check InBody GID & row 3 headers.")

    with tabs[2]:
        st.subheader("Oura Biometrics")
        if not ou_v.empty:
            # Dynamic search for Oura columns
            metrics = []
            for target in ['readiness', 'sleep_score', 'hrv']:
                match = next((c for c in ou_v.columns if target in c.lower()), None)
                if match: metrics.append(match)
            build_master_chart(ou_v, o_date, metrics, "Combined Recovery Trends")
        else: st.warning("Oura data missing.")

    with tabs[3]:
        st.subheader("Master Correlation Timeline")
        fig_master = go.Figure()
        fig_master.add_trace(go.Bar(x=df_v[t_date], y=df_v['STEPS_CLEAN'], name="Steps", marker_color='rgba(0, 255, 204, 0.2)'))
        if not ou_v.empty:
            rk = next((c for c in ou_v.columns if 'readiness' in c.lower()), None)
            if rk: fig_master.add_trace(go.Scatter(x=ou_v[o_date], y=ou_v[rk], name="Readiness", line=dict(color='#FF4B4B', width=4)))
        fig_master.update_layout(template="plotly_dark", height=500)
        st.plotly_chart(fig_master, use_container_width=True)

except Exception as e:
    st.error(f"Intelligence Module Error: {e}")

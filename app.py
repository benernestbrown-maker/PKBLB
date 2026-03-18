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
    /* Style the radio buttons to look like a sleek toggle menu */
    div.row-widget.stRadio > div{flex-direction:row; justify-content: center;}
    </style>
    """, unsafe_allow_html=True)

# GIDs
TRACKER_GID = "0"
OURA_GID = "502032885"
INBODY_GID = "686934394" 
TIMELINE_GID = "REPLACE_ME" # <--- ADD YOUR TIMELINE TAB GID HERE

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

    def get_phases(gid):
        url = f"{BASE_URL}gid={gid}&single=true&output=csv"
        try:
            df = pd.read_csv(url, header=None)
            raw_phases = df.iloc[7:59, 3].tolist() 
            dates, phases = [], []
            start_date = pd.to_datetime("2025-06-23")
            for i, val in enumerate(raw_phases):
                val_str = str(val).strip()
                if val_str.lower() not in ['phase', 'nan', '']:
                    dates.append(start_date + timedelta(days=7*i))
                    phases.append(val_str)
            return pd.DataFrame({'Week_Start': dates, 'Phase': phases})
        except: return pd.DataFrame()

    # --- TRACKER ---
    df = get_df_smart(TRACKER_GID, 4)
    t_date = next((c for c in df.columns if 'DATE' in c.upper()), None)
    if t_date and not df.empty:
        df[t_date] = pd.to_datetime(df[t_date], dayfirst=True, errors='coerce')
        df = df.dropna(subset=[t_date]).sort_values(t_date)
        df = df[df[t_date] <= datetime.now()]
        
        step_col = next((c for c in df.columns if 'STEPS' in c.upper()), df.columns[18] if len(df.columns) > 18 else df.columns[-1])
        df['STEPS_CLEAN'] = pd.to_numeric(df[step_col].astype(str).str.replace('STEPS', '', case=False).str.replace(',', ''), errors='coerce')
        df['BODYWEIGHT (kg)'] = pd.to_numeric(df['BODYWEIGHT (kg)'], errors='coerce')

    # --- OURA ---
    oura = get_df_smart(OURA_GID, 0)
    o_date = None
    if not oura.empty:
        o_date = next((c for c in oura.columns if 'DAY' in c.lower() or 'DATE' in c.upper()), oura.columns[0])
        oura[o_date] = pd.to_datetime(oura[o_date], errors='coerce')
        oura = oura.dropna(subset=[o_date]).sort_values(o_date)
        oura = oura[oura[o_date] <= datetime.now()]

    # --- INBODY ---
    inbody = get_df_smart(INBODY_GID, 2)
    i_date = None
    if not inbody.empty:
        i_date = next((c for c in inbody.columns if 'DATE' in c.upper()), inbody.columns[0])
        inbody[i_date] = pd.to_datetime(inbody[i_date], dayfirst=True, errors='coerce')
        inbody = inbody.dropna(subset=[i_date]).sort_values(i_date)

    phase_df = get_phases(TIMELINE_GID)
    return df, oura, inbody, phase_df, t_date, o_date, i_date

def build_pro_chart(data, x_col, y_cols, title, colors=['#00ffcc', '#FF4B4B', '#9C27B0', '#FFEB3B'], is_bar=False):
    fig = go.Figure()
    actual_cols = []
    for target in y_cols:
        match = next((c for c in data.columns if target.lower() in c.lower()), None)
        if match: actual_cols.append(match)
    
    for i, col in enumerate(actual_cols):
        clean = data.dropna(subset=[col])
        if clean.empty: continue
        
        if is_bar:
            fig.add_trace(go.Bar(x=clean[x_col], y=clean[col], name=col.split('_')[0].title(), marker_color=colors[i%len(colors)]))
        else:
            fig.add_trace(go.Scatter(x=clean[x_col], y=clean[col], name=col.split('_')[0].title(),
                                     line=dict(color=colors[i%len(colors)], width=3, shape='spline'), mode='lines+markers'))
    
    fig.update_layout(template="plotly_dark", title=f"<b>{title}</b>", height=400, 
                      hovermode="x unified", legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)

try:
    df, oura, inbody, phase_df, t_date, o_date, i_date = fetch_all_data()
    
    st.sidebar.title("🎛️ Controls")
    
    # PHASE FILTER
    active_phase = "All Phases"
    if not phase_df.empty:
        phase_options = ["All Phases"] + phase_df['Phase'].unique().tolist()
        active_phase = st.sidebar.selectbox("Filter by Phase", phase_options)

    # TIME WINDOW (Anchored to actual data, not just "today")
    time_choice = st.sidebar.selectbox("Window", ["Week", "Month", "3 Months", "6 Months", "All Time"])
    windows = {"Week": 7, "Month": 30, "3 Months": 90, "6 Months": 180, "All Time": 9999}
    
    # Safely find the absolute latest date recorded to anchor the lookback window
    max_dates = []
    if t_date and not df.empty: max_dates.append(df[t_date].max())
    if o_date and not oura.empty: max_dates.append(oura[o_date].max())
    latest_anchor = max(max_dates) if max_dates else datetime.now()
    start_date = latest_anchor - timedelta(days=windows[time_choice])
    
    # Apply Time Filter
    df_v = df[df[t_date] >= start_date] if t_date and not df.empty else pd.DataFrame()
    ou_v = oura[oura[o_date] >= start_date] if o_date and not oura.empty else pd.DataFrame()
    ib_v = inbody[inbody[i_date] >= start_date] if i_date and not inbody.empty else pd.DataFrame()

    # Apply Phase Filter
    if active_phase != "All Phases" and not phase_df.empty:
        valid_weeks = phase_df[phase_df['Phase'] == active_phase]
        valid_dates = set()
        for _, row in valid_weeks.iterrows():
            valid_dates.update([(row['Week_Start'] + timedelta(days=i)).date() for i in range(7)])
            
        if not df_v.empty: df_v = df_v[df_v[t_date].dt.date.isin(valid_dates)]
        if not ou_v.empty: ou_v = ou_v[ou_v[o_date].dt.date.isin(valid_dates)]
        if not ib_v.empty: ib_v = ib_v[ib_v[i_date].dt.date.isin(valid_dates)]

    st.title("⚡ BEN'S PERFORMANCE HUB")
    st.markdown(f"**Current View:** {active_phase} ({time_choice})")
    
    tabs = st.tabs(["📊 Vitals", "📉 Composition", "😴 Oura Recovery", "📅 Timeline"])

    with tabs[0]:
        c1, c2, c3, c4 = st.columns(4)
        
        # Calculate Averages for the HUD
        if not df_v.empty and 'BODYWEIGHT (kg)' in df_v.columns:
            avg_w = df_v['BODYWEIGHT (kg)'].dropna().mean()
            if pd.notna(avg_w): c1.metric("Avg Weight", f"{avg_w:.1f} kg")
            
        if not df_v.empty and 'STEPS_CLEAN' in df_v.columns:
            avg_s = df_v['STEPS_CLEAN'].dropna().mean()
            if pd.notna(avg_s): c2.metric("Avg Steps", f"{int(avg_s):,}")
        
        hrv_k, readi_k = None, None
        if not ou_v.empty:
            hrv_k = next((c for c in ou_v.columns if 'hrv' in c.lower()), None)
            readi_k = next((c for c in ou_v.columns if 'readiness' in c.lower()), None)
            if hrv_k:
                avg_hrv = ou_v[hrv_k].dropna().mean()
                if pd.notna(avg_hrv): c3.metric("Avg HRV", f"{int(avg_hrv)}ms")
            if readi_k:
                avg_readi = ou_v[readi_k].dropna().mean()
                if pd.notna(avg_readi): c4.metric("Avg Readiness", f"{int(avg_readi)}")
        
        st.divider()
        
        # THE INTERACTIVE GRAPH TOGGLE
        chart_choice = st.radio("Select Trend to Display:", ["Weight", "Steps", "HRV", "Readiness"], horizontal=True)
        
        if chart_choice == "Weight":
            build_pro_chart(df_v, t_date, ['BODYWEIGHT (kg)'], "Weight Trend", ['#00ffcc'])
        elif chart_choice == "Steps":
            build_pro_chart(df_v, t_date, ['STEPS_CLEAN'], "Activity Trend", ['#FF4B4B'], is_bar=True)
        elif chart_choice == "HRV":
            if hrv_k and not ou_v.empty: build_pro_chart(ou_v, o_date, [hrv_k], "HRV Trend", ['#9C27B0'])
            else: st.info("No HRV data available for this window.")
        elif chart_choice == "Readiness":
            if readi_k and not ou_v.empty: build_pro_chart(ou_v, o_date, [readi_k], "Readiness Trend", ['#FFEB3B'])
            else: st.info("No Readiness data available for this window.")

    with tabs[1]:
        st.subheader("InBody Decisive Analysis")
        if not ib_v.empty:
            bf_col = next((c for c in ib_v.columns if 'BF%' in c or 'FAT' in c.upper()), None)
            mm_col = next((c for c in ib_v.columns if 'MUSCLE' in c.upper()), None)
            build_pro_chart(ib_v, i_date, [c for c in [bf_col, mm_col] if c], "Fat % vs Muscle Mass")
        else:
            st.info("Check InBody GID & row 3 headers.")

    with tabs[2]:
        st.subheader("Amalgamated Recovery")
        build_pro_chart(ou_v, o_date, ['readiness', 'sleep_score', 'hrv'], "Readiness vs Sleep vs HRV")
        st.divider()
        st.subheader("Decisive Strain Markers")
        build_pro_chart(ou_v, o_date, ['heart_rate', 'temperature_deviation'], "RHR & Temp Deviation")

    with tabs[3]:
        st.subheader("Activity vs Readiness Correlation")
        fig = go.Figure()
        if not df_v.empty and 'STEPS_CLEAN' in df_v.columns:
            fig.add_trace(go.Bar(x=df_v[t_date], y=df_v['STEPS_CLEAN'], name="Steps", marker_color='rgba(0, 255, 204, 0.3)'))
        if not ou_v.empty:
            readi_k_tl = next((c for c in ou_v.columns if 'readiness' in c.lower()), None)
            if readi_k_tl and readi_k_tl in ou_v.columns:
                valid_tl = ou_v.dropna(subset=[readi_k_tl])
                fig.add_trace(go.Scatter(x=valid_tl[o_date], y=valid_tl[readi_k_tl], name="Readiness", line=dict(color='#FF4B4B', width=4)))
        fig.update_layout(template="plotly_dark", height=500, hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Sync Error: {e}")

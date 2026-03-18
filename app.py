import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page Config
st.set_page_config(page_title="Performance Hub", layout="wide")

# --- CONFIGURATION ---
# UPDATE THESE GIDs based on your browser URL
TRACKER_GID = "0"          # Check the gid for 'Daily Tracker'
OURA_GID = "1547806509"    # Check the gid for 'Oura_Link'
BASE_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRcgV5PFrp4XmAcNn3cutN0PvxKoZGhTY8wc8NKp70wDdajdsrYPOfNWezEBCoX-wSJyGtHSDDMyqse/pub?"

@st.cache_data(ttl=60)
def fetch_data(gid, skip=0):
    url = f"{BASE_URL}gid={gid}&single=true&output=csv"
    df = pd.read_csv(url, skiprows=skip)
    df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
    return df

try:
    # Sidebar Navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Dashboard", "Recovery (Oura)"])

    if page == "Dashboard":
        df = fetch_data(TRACKER_GID, skip=4)
        df = df.dropna(subset=['DATE'])
        df['BODYWEIGHT (kg)'] = pd.to_numeric(df['BODYWEIGHT (kg)'], errors='coerce')
        df['STEPS'] = pd.to_numeric(df['STEPS'].astype(str).str.replace(',', ''), errors='coerce')
        
        latest = df.dropna(subset=['BODYWEIGHT (kg)']).iloc[-1]
        plot_df = df.tail(30)

        st.title("⚡ BEN'S PERFORMANCE HUB")
        
        # Metrics
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Weight", f"{latest['BODYWEIGHT (kg)']}kg")
        steps = int(latest['STEPS']) if not pd.isna(latest['STEPS']) else 0
        c2.metric("Steps", f"{steps:,}", f"{steps - 12500} vs Goal")
        c3.metric("Energy", f"{latest['ENERGY LEVELS Scale 1-10']}/10")
        c4.metric("Sleep", f"{latest['SLEEP QUALITY Sleep Score OR Scale 1-10']}")

        st.divider()

        # Dual Axis Chart
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(x=plot_df['DATE'], y=plot_df['STEPS'], name="Steps", marker_color='rgba(0, 255, 204, 0.2)'), secondary_y=False)
        fig.add_trace(go.Scatter(x=plot_df['DATE'], y=plot_df['BODYWEIGHT (kg)'], name="Weight", line=dict(color='#00ffcc', width=4, shape='spline'), mode='lines+markers'), secondary_y=True)
        
        fig.update_layout(template="plotly_dark", hovermode="x unified", showlegend=False, height=500, margin=dict(l=10, r=10, t=10, b=10))
        fig.update_yaxes(title_text="Steps", secondary_y=False, showgrid=False)
        fig.update_yaxes(title_text="Weight (kg)", secondary_y=True, showgrid=True, gridcolor='rgba(255,255,255,0.1)')
        st.plotly_chart(fig, use_container_width=True)

    elif page == "Recovery (Oura)":
        st.title("😴 Recovery Insights")
        oura_df = fetch_data(OURA_GID)
        
        # HRV and Readiness Trends
        fig_oura = make_subplots(specs=[[{"secondary_y": True}]])
        fig_oura.add_trace(go.Scatter(x=oura_df['day'], y=oura_df['average_hrv'], name="HRV", line=dict(color='#00FFAA', width=3)), secondary_y=False)
        fig_oura.add_trace(go.Scatter(x=oura_df['day'], y=oura_df['readiness_score'], name="Readiness", line=dict(color='#FF4B4B', width=2, dash='dot')), secondary_y=True)
        fig_oura.update_layout(template="plotly_dark", height=500)
        st.plotly_chart(fig_oura, use_container_width=True)

except Exception as e:
    st.error(f"Error: {e}")
    st.info("Check if your Daily Tracker gid is correct (usually 0).")

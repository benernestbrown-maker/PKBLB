import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. Page Config & Dark Theme UI
st.set_page_config(page_title="Ben's PT Hub", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { color: #00ffcc; font-size: 2.2rem; font-weight: 700; }
    div[data-testid="stMetricDelta"] { font-size: 1.1rem; }
    </style>
    """, unsafe_allow_html=True)

# 2. Data Connection
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRcgV5PFrp4XmAcNn3cutN0PvxKoZGhTY8wc8NKp70wDdajdsrYPOfNWezEBCoX-wSJyGtHSDDMyqse/pub?output=csv"

@st.cache_data(ttl=60)
def fetch_and_clean():
    # Skip the first 4 rows to hit the actual headers
    df = pd.read_csv(CSV_URL, skiprows=4)
    df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
    
    # Filter for rows that actually have data
    df = df.dropna(subset=['DATE'])
    df['BODYWEIGHT (kg)'] = pd.to_numeric(df['BODYWEIGHT (kg)'], errors='coerce')
    df['STEPS'] = pd.to_numeric(df['STEPS'].astype(str).str.replace(',', ''), errors='coerce')
    
    # We only care about the last 30 entries for the visual trend
    return df

try:
    df = fetch_and_clean()
    # Grab the last row for the metric cards
    latest = df.dropna(subset=['BODYWEIGHT (kg)']).iloc[-1]
    plot_df = df.tail(30) # The last 30 days for the graph

    st.title("⚡ BEN'S PERFORMANCE HUB")

    # --- TOP ROW: KPI CARDS ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Bodyweight", f"{latest['BODYWEIGHT (kg)']}kg")
    
    step_val = int(latest['STEPS']) if not pd.isna(latest['STEPS']) else 0
    c2.metric("Steps", f"{step_val:,}", f"{step_val - 12500} vs Goal")
    
    c3.metric("Energy Level", f"{latest['ENERGY LEVELS Scale 1-10']}/10")
    c4.metric("Sleep Quality", f"{latest['SLEEP QUALITY Sleep Score OR Scale 1-10']}")

    st.divider()

    # --- THE "PRO" CHART: DUAL AXIS ---
    st.subheader("📊 Weight Trend vs. Daily Activity")
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add Steps as Bars (Background)
    fig.add_trace(
        go.Bar(
            x=plot_df['DATE'], 
            y=plot_df['STEPS'], 
            name="Steps", 
            marker_color='rgba(0, 255, 204, 0.2)', # Faint Neon Green
            hovertemplate='%{y} steps'
        ),
        secondary_y=False,
    )

    # Add Weight as a Thick Line (Foreground)
    fig.add_trace(
        go.Scatter(
            x=plot_df['DATE'], 
            y=plot_df['BODYWEIGHT (kg)'], 
            name="Weight (kg)",
            line=dict(color='#00ffcc', width=4, shape='spline'), # Smooth curved line
            mode='lines+markers',
            marker=dict(size=8),
            hovertemplate='%{y}kg'
        ),
        secondary_y=True,
    )

    # Chart Styling
    fig.update_layout(
        template="plotly_dark",
        hovermode="x unified",
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        height=500
    )

    # Fix the axes so they don't overlap weirdly
    fig.update_yaxes(title_text="Steps", secondary_y=False, showgrid=False)
    fig.update_yaxes(title_text="Weight (kg)", secondary_y=True, showgrid=True, gridcolor='rgba(255,255,255,0.1)')

    st.plotly_chart(fig, use_container_width=True)

    # --- PT FEEDBACK ---
    st.divider()
    with st.expander("💬 View Recent Daily Comments"):
        notes = df.dropna(subset=['DAILY COMMENTS']).tail(7)
        for _, row in notes.iterrows():
            st.write(f"**{row['DATE']}:** {row['DAILY COMMENTS']}")

except Exception as e:
    st.error(f"Waiting for your spreadsheet to update... Error: {e}")

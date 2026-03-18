import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. Expert UI Configuration
st.set_page_config(page_title="Ben's Performance Command Centre", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { color: #00ffcc; font-size: 2.2rem; font-weight: 800; }
    .stPlotlyChart { border: 1px solid #30363d; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Data Engine
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRcgV5PFrp4XmAcNn3cutN0PvxKoZGhTY8wc8NKp70wDdajdsrYPOfNWezEBCoX-wSJyGtHSDDMyqse/pub?output=csv"

@st.cache_data(ttl=60)
def load_and_refine_data():
    # Load Daily Tracker (Skip the spreadsheet headers)
    df = pd.read_csv(CSV_URL, skiprows=4)
    df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
    
    # Filter only rows that have a valid date and drop "future" placeholder rows
    df = df.dropna(subset=['DATE'])
    
    # Convert all training metrics to numeric, handling commas and strings
    metrics = {
        'Weight': 'BODYWEIGHT (kg)',
        'Steps': 'STEPS',
        'Energy': 'ENERGY LEVELS Scale 1-10',
        'Sleep': 'SLEEP QUALITY Sleep Score OR Scale 1-10',
        'Stress': 'STRESS LEVELS Scale 1-10'
    }
    
    for key, col in metrics.items():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
    
    return df, metrics

def build_pro_chart(df, col_name, title, color, chart_type="line"):
    # Clean data specifically for this chart to avoid "gaps" or zero-drops
    plot_df = df.dropna(subset=[col_name])
    if plot_df.empty: return None
    
    fig = go.Figure()
    if chart_type == "bar":
        fig.add_trace(go.Bar(x=plot_df['DATE'], y=plot_df[col_name], marker_color=color, name=title))
    else:
        fig.add_trace(go.Scatter(x=plot_df['DATE'], y=plot_df[col_name], 
                                 line=dict(color=color, width=4, shape='spline'),
                                 mode='lines+markers', marker=dict(size=6)))
    
    fig.update_layout(
        template="plotly_dark", title=f"<b>{title}</b>",
        height=300, margin=dict(l=10, r=10, t=40, b=10),
        hovermode="x unified", showlegend=False
    )
    return fig

try:
    df, metrics = load_and_refine_data()
    
    st.title("⚡ BEN'S PERFORMANCE COMMAND CENTRE")
    
    # --- SECTION 1: TODAY'S VITALS ---
    latest = df.dropna(subset=[metrics['Weight']]).iloc[-1]
    m1, m2, m3, m4, m5 = st.columns(5)
    
    m1.metric("Weight", f"{latest[metrics['Weight']]}kg")
    
    curr_steps = int(latest[metrics['Steps']]) if not pd.isna(latest[metrics['Steps']]) else 0
    m2.metric("Steps", f"{curr_steps:,}", f"{curr_steps - 12500} vs Goal")
    
    m3.metric("Energy", f"{latest[metrics['Energy']]}/10")
    m4.metric("Sleep", f"{latest[metrics['Sleep']]}")
    m5.metric("Stress", f"{latest[metrics['Stress']]}/10")

    st.divider()

    # --- SECTION 2: THE DATA GRID (No more busy charts) ---
    col_left, col_right = st.columns(2)

    with col_left:
        # Weight Graph
        w_fig = build_pro_chart(df, metrics['Weight'], "Bodyweight Trend (kg)", "#00ffcc")
        if w_fig: st.plotly_chart(w_fig, use_container_width=True)
        
        # Energy Graph
        e_fig = build_pro_chart(df, metrics['Energy'], "Daily Energy Levels", "#FFEB3B")
        if e_fig: st.plotly_chart(e_fig, use_container_width=True)

    with col_right:
        # Steps Graph with Goal Line
        s_fig = build_pro_chart(df, metrics['Steps'], "Daily Step Activity", "#FF4B4B", "bar")
        if s_fig:
            s_fig.add_hline(y=12500, line_dash="dash", line_color="white", annotation_text="12.5k Goal")
            st.plotly_chart(s_fig, use_container_width=True)
            
        # Stress Graph
        st_fig = build_pro_chart(df, metrics['Stress'], "Stress Markers", "#FF9800")
        if st_fig: st.plotly_chart(st_fig, use_container_width=True)

    # --- SECTION 3: COACHING & RECOVERY BITS ---
    st.divider()
    c_a, c_b = st.columns(2)
    
    with c_a:
        st.subheader("📝 Daily PT Feedback")
        notes = df.dropna(subset=['DAILY COMMENTS']).tail(5)
        for _, row in notes.iterrows():
            st.info(f"**{row['DATE']}**: {row['DAILY COMMENTS']}")

    with c_b:
        st.subheader("💡 Expert Recommendations")
        # Personalised logic based on your home setup
        if latest[metrics['Stress']] > 7:
            st.warning("⚠️ Stress is high. Allocate 15 mins for the **Shakti Mat** tonight.")
        if latest[metrics['Energy']] < 5:
            st.error("📉 Low Energy detected. PT Note: Check 'Ultra' Baked Oats—ensure +20ml milk to fix the dryness.")
        else:
            st.success("✅ Metrics looking stable. Maintain current training volume.")

except Exception as e:
    st.error(f"Waiting for your sheet to sync... (Ensure Daily Tracker is tab 1). Error: {e}")

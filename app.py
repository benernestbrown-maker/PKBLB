import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Page Config
st.set_page_config(page_title="Performance Hub", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { color: #00ffcc; font-size: 2.2rem; }
    </style>
    """, unsafe_allow_html=True)

# 2. Data Connection (Entire Document Link)
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRcgV5PFrp4XmAcNn3cutN0PvxKoZGhTY8wc8NKp70wDdajdsrYPOfNWezEBCoX-wSJyGtHSDDMyqse/pub?output=csv"

@st.cache_data(ttl=60)
def load_and_clean():
    # Load Daily Tracker (Skip the headers)
    df = pd.read_csv(CSV_URL, skiprows=4)
    df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
    
    # Keep only rows with a date
    df = df.dropna(subset=['DATE'])
    
    # Clean up numeric columns
    df['BODYWEIGHT (kg)'] = pd.to_numeric(df['BODYWEIGHT (kg)'], errors='coerce')
    df['STEPS'] = pd.to_numeric(df['STEPS'].astype(str).str.replace(',', ''), errors='coerce')
    
    return df

try:
    df = load_and_clean()
    
    # Filter for ONLY rows with actual data so the graph isn't 'busy' with zeros
    weight_df = df.dropna(subset=['BODYWEIGHT (kg)'])
    steps_df = df.dropna(subset=['STEPS'])
    
    st.title("⚡ BEN'S PERFORMANCE HUB")

    # --- TOP ROW: STATS ---
    if not weight_df.empty:
        latest = weight_df.iloc[-1]
        c1, c2, c3 = st.columns(3)
        c1.metric("Bodyweight", f"{latest['BODYWEIGHT (kg)']}kg")
        
        step_val = int(latest['STEPS']) if not pd.isna(latest['STEPS']) else 0
        c2.metric("Latest Steps", f"{step_val:,}", f"{step_val - 12500} vs Goal")
        c3.metric("Energy", f"{latest['ENERGY LEVELS Scale 1-10']}/10")

    st.divider()

    # --- THE GRAPHS (SPLIT FOR CLARITY) ---
    
    # Chart 1: Weight Trend
    st.subheader("📉 Bodyweight Progress (kg)")
    if not weight_df.empty:
        fig_weight = go.Figure()
        fig_weight.add_trace(go.Scatter(
            x=weight_df['DATE'], 
            y=weight_df['BODYWEIGHT (kg)'],
            line=dict(color='#00ffcc', width=4, shape='spline'),
            mode='lines+markers',
            name="Weight"
        ))
        fig_weight.update_layout(template="plotly_dark", height=350, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_weight, use_container_width=True)

    # Chart 2: Step Activity
    st.subheader("🏃 Daily Step Count")
    if not steps_df.empty:
        fig_steps = go.Figure()
        fig_steps.add_trace(go.Bar(
            x=steps_df['DATE'], 
            y=steps_df['STEPS'],
            marker_color='#FF4B4B',
            name="Steps"
        ))
        # Add a Goal Line at 12,500
        fig_steps.add_hline(y=12500, line_dash="dash", line_color="white", annotation_text="Goal")
        fig_steps.update_layout(template="plotly_dark", height=350, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_steps, use_container_width=True)

    # --- PT NOTES ---
    st.divider()
    with st.expander("📝 View Recent Training Comments"):
        notes = df.dropna(subset=['DAILY COMMENTS']).tail(5)
        for _, row in notes.iterrows():
            st.info(f"**{row['DATE']}**: {row['DAILY COMMENTS']}")

except Exception as e:
    st.error(f"Waiting for data... Ensure 'Daily Tracker' is the first tab in your sheet. Error: {e}")

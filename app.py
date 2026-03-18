import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Page Setup
st.set_page_config(page_title="Ben's Performance Hub", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { color: #00ffcc; font-size: 2rem; }
    .stPlotlyChart { border-radius: 10px; overflow: hidden; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRcgV5PFrp4XmAcNn3cutN0PvxKoZGhTY8wc8NKp70wDdajdsrYPOfNWezEBCoX-wSJyGtHSDDMyqse/pub?output=csv"

@st.cache_data(ttl=60)
def load_and_clean():
    # Load and find the data row
    df = pd.read_csv(CSV_URL, skiprows=4)
    df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
    df = df.dropna(subset=['DATE'])
    
    # Convert all metrics to numbers safely
    cols_to_fix = ['BODYWEIGHT (kg)', 'STEPS', 'ENERGY LEVELS Scale 1-10', 
                   'SLEEP QUALITY Sleep Score OR Scale 1-10', 'STRESS LEVELS Scale 1-10']
    
    for col in cols_to_fix:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
    
    return df

def create_graph(data, x_col, y_col, title, color, is_bar=False):
    # Only plot if there is actually data for this metric
    plot_data = data.dropna(subset=[y_col])
    if plot_data.empty:
        return None
        
    fig = go.Figure()
    if is_bar:
        fig.add_trace(go.Bar(x=plot_data[x_col], y=plot_data[y_col], marker_color=color, name=title))
    else:
        fig.add_trace(go.Scatter(x=plot_data[x_col], y=plot_data[y_col], line=dict(color=color, width=3, shape='spline'), mode='lines+markers', name=title))
    
    fig.update_layout(template="plotly_dark", title=title, height=300, margin=dict(l=20, r=20, t=40, b=20), hovermode="x unified")
    return fig

try:
    df = load_and_clean()
    st.title("⚡ BEN'S PERFORMANCE HUB")
    st.write("---")

    # --- ROW 1: PRIMARY PHYSICAL DATA ---
    col1, col2 = st.columns(2)
    
    with col1:
        weight_fig = create_graph(df, 'DATE', 'BODYWEIGHT (kg)', "Bodyweight Trend (kg)", "#00ffcc")
        if weight_fig: st.plotly_chart(weight_fig, use_container_width=True)
        
    with col2:
        steps_fig = create_graph(df, 'DATE', 'STEPS', "Daily Step Count", "#FF4B4B", is_bar=True)
        if steps_fig: 
            steps_fig.add_hline(y=12500, line_dash="dash", line_color="white")
            st.plotly_chart(steps_fig, use_container_width=True)

    # --- ROW 2: BIOFEEDBACK DATA ---
    col3, col4, col5 = st.columns(3)
    
    with col3:
        energy_fig = create_graph(df, 'DATE', 'ENERGY LEVELS Scale 1-10', "Energy Levels (1-10)", "#FFEB3B")
        if energy_fig: st.plotly_chart(energy_fig, use_container_width=True)
        
    with col4:
        sleep_fig = create_graph(df, 'DATE', 'SLEEP QUALITY Sleep Score OR Scale 1-10', "Sleep Quality", "#9C27B0")
        if sleep_fig: st.plotly_chart(sleep_fig, use_container_width=True)
        
    with col5:
        stress_fig = create_graph(df, 'DATE', 'STRESS LEVELS Scale 1-10', "Stress Levels (1-10)", "#FF9800")
        if stress_fig: st.plotly_chart(stress_fig, use_container_width=True)

    # --- ROW 3: RECENT FEEDBACK ---
    st.divider()
    with st.expander("📝 View Recent Training Notes"):
        notes = df.dropna(subset=['DAILY COMMENTS']).tail(5)
        for _, row in notes.iterrows():
            st.info(f"**{row['DATE']}**: {row['DAILY COMMENTS']}")

except Exception as e:
    st.error(f"Waiting for data... Ensure 'Daily Tracker' is the first tab. Error: {e}")

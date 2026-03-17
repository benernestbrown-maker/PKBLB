import streamlit as st
import pandas as pd

# App Title
st.set_page_config(page_title="PT Performance Dashboard", layout="wide")
st.title("🚀 Performance Tracker")

# 1. Load Data (Replace 'your_csv_link' with your published Google Sheet CSV link)
# Tip: In Google Sheets, go to File > Share > Publish to Web > Select 'Daily Tracker' as CSV
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRcgV5PFrp4XmAcNn3cutN0PvxKoZGhTY8wc8NKp70wDdajdsrYPOfNWezEBCoX-wSJyGtHSDDMyqse/pub?gid=0&single=true&output=csv"

@st.cache_data
def load_data(url):
    df = pd.read_csv(url)
    return df

try:
    df = load_data(sheet_url)

    # 2. Key Metrics Row
    latest = df.iloc[-1] # Gets the most recent entry
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Weight", f"{latest['BODYWEIGHT (kg)']} kg")
    col2.metric("Steps", f"{latest['STEPS']}")
    col3.metric("Sleep Score", f"{latest['SLEEP QUALITY']}")
    col4.metric("Energy", f"{latest['ENERGY LEVELS (1-10)']}/10")

    # 3. Visuals
    st.subheader("Weight Trend")
    st.line_chart(df.set_index('DATE')['BODYWEIGHT (kg)'])

    st.subheader("Steps vs Target")
    st.bar_chart(df.set_index('DATE')['STEPS'])

except:
    st.error("Connect your Google Sheet CSV URL to see data.")

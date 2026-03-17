import streamlit as st
import pandas as pd

st.set_page_config(page_title="Ben's PT Dashboard", layout="wide")

# The confirmed CSV link
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRcgV5PFrp4XmAcNn3cutN0PvxKoZGhTY8wc8NKp70wDdajdsrYPOfNWezEBCoX-wSJyGtHSDDMyqse/pub?gid=0&single=true&output=csv"

def load_data():
    # We skip 4 rows because your data starts on Row 5
    df = pd.read_csv(CSV_URL, skiprows=4)
    # Clean up column names to handle line breaks and spaces
    df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
    # Filter out empty rows
    df = df.dropna(subset=['DATE'])
    return df

try:
    df = load_data()
    
    st.title("🚀 Ben's Performance Dashboard")
    
    # Get the last row that has a weight entry
    valid_weight = df.dropna(subset=['BODYWEIGHT (kg)'])
    
    if not valid_weight.empty:
        latest = valid_weight.iloc[-1]
        
        # 1. Headline Stats
        m1, m2, m3 = st.columns(3)
        m1.metric("Current Weight", f"{latest['BODYWEIGHT (kg)']} kg")
        m2.metric("Latest Steps", f"{latest['STEPS']}")
        m3.metric("Energy Level", f"{latest['ENERGY LEVELS Scale 1-10']}/10")

        st.divider()

        # 2. Charts
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("Weight Progress")
            # Only graph rows that have a weight value
            st.line_chart(data=valid_weight, x='DATE', y='BODYWEIGHT (kg)')

        with col_right:
            st.subheader("Daily Steps")
            # Convert steps to numbers just in case there are commas
            df['STEPS_NUM'] = pd.to_numeric(df['STEPS'].astype(str).str.replace(',', ''), errors='coerce')
            st.bar_chart(data=df.dropna(subset=['STEPS_NUM']), x='DATE', y='STEPS_NUM')
    else:
        st.info("App connected! Waiting for you to enter data into the 'BODYWEIGHT' column of your sheet.")

except Exception as e:
    st.error(f"Almost there! The app is having trouble reading the columns. Error: {e}")

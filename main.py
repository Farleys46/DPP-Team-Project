import streamlit as st
import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv


load_dotenv()


st.set_page_config(page_title="Sthlm Air & Flight Tracker", layout="wide")
st.title("Air traffic vs Air Quality in Stockholm")

if st.button("Load latest data"):
    st.rerun()

def load_data():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "db"),
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD")
        )
# Query för att hämta enkel data från air_quality tabellen.
        query = """
            SELECT db_timestamp as timestamp, value as aqi, parameter 
            FROM air_quality 
            WHERE parameter = 'pm10'
            ORDER BY db_timestamp DESC 
            LIMIT 50
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

df = load_data()

if not df.empty:
    # --- WARNING SYSTEM ---
    latest_aqi = df.iloc[0]['aqi']
    
    if latest_aqi > 50:
        st.error(f"Warning: High Particle Levels! ({latest_aqi})")
    elif latest_aqi > 35:
        st.warning(f"Moderate air quality ({latest_aqi})")
    else:
        st.success(f"Good air quality ({latest_aqi})")

    st.write("### Latest collected PM10 data")
    st.dataframe(df.head(10))

    st.write("### Air Quality Trends over time")
    # Sätter tidsstämpeln som index för att grafen ska bli rätt
    df.set_index('timestamp', inplace=True)
    st.line_chart(df[['aqi']])
    
else:
    st.warning("No data available to display. Please wait a few minutes and refresh the page!")
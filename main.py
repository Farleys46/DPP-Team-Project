def main():
    print("Hello from dpp-team-project!")


if __name__ == "__main__":
    main()


# Streamlit dashboard, gör en pull och kör en "pip install requirements.txt" i terminalen eller en "pip install streamlit" direkt i terminalen om det bara är den som fattas...
import streamlit as st
import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

### config lines to be included, e.g. ...
st.set_page_config(page_title="Sthlm Air & Flight Tracker", layout="wide")
st.title("Air traffic vs Air Quality in Stockholm")
if st.button("Load latest data"):
    st.rerun()

def load_data():
    try:
        conn = psycopg2.conncet(
            host=os.getenv("DB_HOST", "db"),
            database=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD")
        )

        query = "SELECT timestamp, flights, aqi_pm25 FROM metrics order BY timestamp DESC"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

df = load_data()

if not df.empty:
    # --- WARNING SYSTEM ---
    latest_aqi = df.iloc[0]['aqi_pm25']
    if latest_aqi > 15:
        st.error(f"Warning: High Particle Levels! ({latest_aqi})")
    elif latest_aqi > 5:
        st.warning(f"Moderate air quality ({latest_aqi})")
    else:
        st.success(f"Good air quality ({latest_aqi})")


    st.write("### Latest collected data")
    st.dataframe(df.head(10))

    st.write("### Trends over time")
    # Graphing code here, e.g. using st.line_chart...
    df.set_index('timestamp', inplace=True)
    st.line_chart(df[['flights', 'aqi_pm25']])
else:
    st.warning("No data available to display. Please wait a few minutes and refresh the page!")


import streamlit as st
import pandas as pd
import psycopg2
import os
import matplotlib.pyplot as plt
import seaborn as sb
from dotenv import load_dotenv


load_dotenv()


st.set_page_config(page_title="SkySense", layout="wide", initial_sidebar_state="collapsed")

# CSS för att anpassa utseendet
st.markdown("""
            <style>
            .block-container { padding-top: 1.5rem;}
            </style>
            """, unsafe_allow_html=True)

# HEADER
st.title("Air traffic vs Air Quality in Stockholm")
st.markdown("Flygtrafik och luftkvalitet över Sthlm/Arlanda")

if st.button("Ladda in senaste datan"):
    st.rerun()

# -- Databasanslutning och SQL query för att joina båda tabellerna.
@st.cache_data(ttl=120)
def load_data():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "db"),
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD")
        )
# Query för att joina air_quality och flight_data baserat på tidsintervall
        trend_query = """
            WITH flight_stats AS (
                SELECT date_trunc("hour", timestamp) AS time_bucket, COUNT(DISTINCT callsign) AS flights
                FROM live_flights GROUP BY time_bucket
                ),
            aq_stats AS (
                SELECT date_trunc("hour", db_timestamp) AS time_bucket, AVG(value) AS pm10
                FROM air_quality WHERE parameter = "pm10" GROUP BY time_bucket
                )
            SELECT COALESCE(f.time_bucket, a.time_bucket) AS timestamp,
                COALESCE(f.flights, 0) AS flights,
                ROUND(COALESCE(a.pm10, 0)::numeric, 1) AS pm10
            FROM flight_stats f
            FULL OUTER JOIN aq_stats a ON f.time_bucket = a.time_bucket
            ORDER BY timestamp DESC LIMIT 24;
        """
        df_trend = pd.read_sql(trend_query, conn)
        
        df_latest_aq = pd.read_sql("SELECT value FROM air_quality WHERE parameter = 'pm10' ORDER BY db_timestamp DESC LIMIT 1", conn)
        df_latest_flights = pd.read_sql("SELECT COUNT(DISTINCT callsign) as count FROM live_flights WHERE timestamp >= NOW() - INTERVAL '15 minutes'", conn)
        
        # Hämta koordinater till en kartfunktion
        df_map = pd.read_sql("SELECT latitude as lat, longitude as lon FROM live_flights WHERE timestamp >= NOW() - INTERVAL '10 minutes' AND latitude IS NOT NULL", conn)
        
        # Stäng anslutningen
        conn.close()
        return df_trend, df_latest_aq, df_latest_flights, df_map
        
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# Ladda in all data
df_trend, df_latest_aq, df_latest_flights, df_map = load_data()

# Layout för dashboarden
if not df_trend.empty:
    
    current_pm10 = df_latest_aq.iloc[0]['value'] if not df_latest_aq.empty else 0
    current_flights = df_latest_flights.iloc[0]['count'] if not df_latest_flights.empty else 0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="✈️ Flyg över Stockholm/Arlanda", value=f"{current_flights}", delta="Aktiva just nu")
        
    with col2:
        #Färga texten baserat på PM10-nivån
        if current_pm10 > 50:
            delta_text = "Höga partikelnivåer!"
            delta_color = "red"
        
        elif current_pm10 > 35:
            delta_text = "Måttlig luftkvalitet"
            delta_color = "orange"
            
        else:
            delta_text = "Bra luftkvalitet"
            delta_color = "green"
            
        st.metric(label="PM10 (luftpartiklar)", value=f"{current_pm10} µg/m³", delta=delta_text, delta_color=delta_color)
        
    with col3:
        st.write("## Flyg över Sthlm/Arlanda (live)##")
        if not df_map.empty:
            st.map(df_map, zoom=7)
        else:
            st.info("Inga plan hittades")
            
    st.markdown("---")
    
    # Rad 2: Graf trenden över tid
    
    col4, col5 = st.columns([2, 1]) # 2/3 av bredden tas up av columnen
    
    with col4:
        st.write("### Utveckling - Senaste 24 timmarna")
        
        # Matplotlib
        sb.set_theme(style="darkgrid")
        fig, ax1 = plt.subplots(figsize=(10, 4))
        df_reversed = df_trend.iloc[::-1]
        
        # Axel 1 Flygplan
        ax1.plot(df_reversed["timestamp"], df_reversed["flights"], color="#00d4ff", marker="o", linewidth=2, label="Flygplan")
        ax1.set_xlabel("Tidpunkt", color="white")
        ax1.set_ylabel("Antal Flygplan", color="#00d4ff", fontweight="bold")
        ax1.tick_params(axis='y', labelcolor="#00d4ff")
        ax1.tick_params(axis='x', colors="white", rotation=45)
        
        # Axel 2 PM10 Grönfärgat
        
        ax2 = ax1.twinx()
        ax2.plot(df_reversed["timestamp"], df_reversed["pm10"], color="#00ff90", marker="s", linewidth=2, label="PM10 (µg/m³)")
        ax2.set_ylabel("PM10 (µg/m³)", color="#00ff90", fontweight="bold")
        ax2.tick_params(axis='y', labelcolor="#00ff90")
        
        # Design och bakgrun
        fig.patch.set_alpha(0.0)
        ax1.set_facecolor("#0e1117")
        ax1.grid(color="#ffffff", alpha=0.1)
        
        lines_1, labels_1 = ax1.get_legend_handles_labels()
        lines_2, labels_2 = ax2.get_legend_handles_labels()
        ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc="upper left")
        
        plt.tight_layout()
        st.pyplot(fig)
        
    with col5:
        st.write("### Senaste datapunkter")
        # Städning för tabellen
        display_df = df_trend.copy()
        display_df["timestamp"] = pd.to_datetime(display_df["timestamp"]).dt.strftime('%H:%M')
        display_df.rename(columns={"timestamp": "Tid", "flights": "Flyg", "pm10": "PM10"}, inplace=True)
        st.dataframe(display_df.head(10), use_container_width=True, hide_index=True)
        
else:
    st.warning("Database is collecting data, please wait a moment and refresh...")

import os
import psycopg2
import time
from dotenv import load_dotenv
from opensky_api import OpenSkyApi

# Hämta API-nyckel och databas inloggning från .env-filen.
load_dotenv()


def get_and_store_flights():
    print("Hämtar flygdata från OpenSky API...")
    
    api = OpenSkyApi()
    
    bbox_arlanda_stockholm = (59.2, 59.8, 17.5, 18.5)
    
    # Hämta flygdata i en box samma som OpenAQ-API.
    s = api.get_states(bbox=(bbox_arlanda_stockholm))
    
    
    if s is None or s.states is None:
        print({ 
            "status": "error",
            "message": "Inga flyg hittades, eller har 10sek Rate Limit inträffat."})
        return
    
    # Transformera datan. 
    flight_data = []
    
    for flight in s.states:
        flight_data.append({
            "callsign": flight.callsign.strip() if flight.callsign else "Unknown",
            "country": flight.origin_country,
            "longitude": flight.longitude,
            "latitude": flight.latitude,
            "altitude_meters": flight.baro_altitude,
            "velocity_m_s": flight.velocity,
            "flight_on_ground": flight.on_ground
        })
    
    
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS live_flights (
                id SERIAL PRIMARY KEY,
                callsign VARCHAR(50),
                country VARCHAR(100),
                longitude FLOAT,
                latitude FLOAT,
                altitude_meters FLOAT,
                velocity_m_s FLOAT,
                flight_on_ground BOOLEAN,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit() # Spara tabelln skapandet
        
        for flight in flight_data:
            insert_query = """
                INSERT INTO live_flights 
                (callsign, country, longitude, latitude, altitude_meters, velocity_m_s, flight_on_ground)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            data_to_insert = (
                flight["callsign"], flight["country"], flight["longitude"], 
                flight["latitude"], flight["altitude_meters"], 
                flight["velocity_m_s"], flight["flight_on_ground"]
            )
            cursor.execute(insert_query, data_to_insert)
            
        conn.commit()
        print(f"Sparade {len(flight_data)} flygplan framgångsrikt i PostgreSQL!")
        
    except Exception as e:
        print(f"Ett fel uppstod med databasen: {e}")
        
    
    finally:
        # Stäng anslutningen för att inte låsa databasen
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

# Startar scriptet
if __name__ == "__main__":
    while True:
        get_and_store_flights()
        print("Klar, väntar 5min innan nästa hämtning av data!")
        time.sleep(300)
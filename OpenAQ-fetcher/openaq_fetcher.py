import os
import requests
import psycopg2
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

# Laddar in .env-filen
load_dotenv()

def get_and_store_air_quality():
    print("Hämtar luftkvalitetsdata från OpenAQ API...")
    
    url = "https://api.openaq.org/v3/locations"
    
    headers = {
        "X-API-Key": os.getenv("OPENAQ_API_KEY")
    }
    
    params = {
        "bbox": "17.5,59.2,18.5,59.8",
        "limit": 50
    }
    
    response = requests.get(url, headers=headers, params=params)   
    
    if response.status_code != 200:
        print(f"Fel vid hämtning: {response.status_code}")
        return
    
    locations_data = response.json().get("results", [])
    
    active_stations = []
    now = datetime.now(timezone.utc)
    
    for location in locations_data:
        last_updated_str = location.get("datetimeLast", {}).get("utc")
        
        if last_updated_str:
            last_updated_dt = datetime.fromisoformat(last_updated_str.replace("Z", "+00:00"))
            
            if now - last_updated_dt < timedelta(hours=24):
                active_stations.append(location)
                
        if len(active_stations) == 10:
            break
            
    dashboard_data = []
    
    for station in active_stations:
        station_id = station["id"]
        
        sensor_map = {}
        for sensor in station.get("sensors", []):
            sensor_map[sensor["id"]] = {
                "parameter": sensor["parameter"]["name"],
                "units": sensor["parameter"]["units"]
            }
        
        url_latest = f"https://api.openaq.org/v3/locations/{station_id}/latest"
        latest_response = requests.get(url_latest, headers=headers)
        
        measurements = []
        if latest_response.status_code == 200:
            latest_data = latest_response.json().get("results", [])
            for m in latest_data:
                sensor_id = m.get("sensorsId")
                value = m.get("value")
                
                sensor_info = sensor_map.get(sensor_id)
                if sensor_info:
                    measurements.append({
                        "parameter": sensor_info["parameter"],
                        "value": value,
                        "units": sensor_info["units"]
                    })
                    
        dashboard_data.append({
            "station_name": station["name"],
            "city": station.get("locality", "Okänd"),
            "latitude": station["coordinates"]["latitude"],
            "longitude": station["coordinates"]["longitude"],
            "last_updated": station["datetimeLast"]["local"],
            "measurements": measurements
        })
        
    if not dashboard_data:
        print("Ingen data att spara.")
        return
    
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
        cursor = conn.cursor()
        
        # Skapa tabellerna direkt i databasen om de inte redan finns
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS air_quality (
                id SERIAL PRIMARY KEY,
                station_name VARCHAR(150),
                city VARCHAR(100),
                latitude FLOAT,
                longitude FLOAT,
                parameter VARCHAR(50),
                value FLOAT,
                units VARCHAR(20),
                last_updated TIMESTAMP,
                db_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        
        # Spara data i databasen
        for station in dashboard_data:
            for measurement in station["measurements"]:
                
                insert_query = """
                    INSERT INTO air_quality (station_name, city, latitude, longitude, parameter, value, units, last_updated)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                data_to_insert = (
                    station["station_name"], 
                    station["city"], 
                    station["latitude"], 
                    station["longitude"], 
                    measurement["parameter"], 
                    measurement["value"], 
                    measurement["units"],
                    station["last_updated"]
                )
                cursor.execute(insert_query, data_to_insert)
                
        conn.commit()
        print(f"Sparade data för {len(dashboard_data)} stationer i databasen!")
        
    except Exception as e:
        print(f"Ett fel uppstod med databasen: {e}")
        
    finally:
        # Viktigt! Stäng anslutningen
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    get_and_store_air_quality()
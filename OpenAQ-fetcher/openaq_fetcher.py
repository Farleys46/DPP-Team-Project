import requests
from fastapi import FastAPI
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import os
import psycopg2

load_dotenv()

def get_and_store_air_quality():
    print("Hämtar luftkvalitetsdata från OpenAQ API...")
    
    url = "https://api.openaq.org/v3/locations"
    
    headers = {
        "X-API-Key": os.getenv("OPENAQ_API_KEY")
    }
    
    params = {
        "bbox": "17.5,59.2,18.5,59.8",
        "limit": 50 # Hämtar max 5 luftkvalitet stationer för att testa.
    }
    
    
    response = requests.get(url, headers=headers, params=params)   
    
    if response.status_code != 200:
        print(f"Fel vid hämtning: {response.status_code}")
        return
    
    locations_data = response.json().get("results", [])
    
    # Filtrera fram 10 Aktiva stationer (Uppdaterade data inom senaste 24 timmarna)
    
    active_stations = []
    now = datetime.now(timezone.utc)
    
    for location in locations_data:
        last_updated_str = location.get("datetimeLast", {}).get("utc")
        
        if last_updated_str:
            last_updated_dt = datetime.fromisoformat(last_updated_str.replace("Z", "+00:00"))
            
            if now - last_updated_dt < timedelta(hours=24):
                active_stations.append(location)
                
        if len (active_stations) == 10:
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
        # Connect to PostgreSQL database and load data.
        conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
        cursor = conn.cursor()
        
        for station in dashboard_data:
            for measurement in station["measurements"]:
                """INSERT INTO 
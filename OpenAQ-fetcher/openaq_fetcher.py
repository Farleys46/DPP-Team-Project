import requests
from fastapi import FastAPI
from datetime import datetime, timezone, timedelta
from openaq_API_KEY import OPENAQ_API_KEY

app = FastAPI()

@app.get("/air-quality")
def get_air_quality():
    
    url = "https://api.openaq.org/v3/locations"
    
    headers = {
        "X-API-Key": OPENAQ_API_KEY
    }
    
    params = {
        "bbox": "17.5,59.2,18.5,59.8",
        "limit": 50 # Hämtar max 5 luftkvalitet stationer för att testa.
    }
    
    
    response = requests.get(url, headers=headers, params=params)   
    
    if response.status_code != 200:
        return {"error": "Kunde inte hämta luftdata", "status_code": response.status_code}
    
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
        
    return {
        "status": "success",
        "active_stations_found": len(dashboard_data),
        "data": dashboard_data
    }
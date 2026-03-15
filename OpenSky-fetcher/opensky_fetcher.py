import os
import psycopg2
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
        print("status": "os.error", "message": "Inga flyg hittades, eller har 10sek Rate Limit inträffat.")
    
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
    
    return {
        "status": "success",
        "total_flights": len(flight_data),
        "data": flight_data
    }
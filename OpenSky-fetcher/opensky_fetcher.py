from fastapi import FastAPI
import requests
from opensky_api import OpenSkyApi
import time

api = OpenSkyApi()

# 3. 
s = api.get_states(time_secs=0, bbox=(58.8, 59.9, 17.0, 19.0))

if s is not None and s.states is not None:
    
    # 3. Loopa igenom s.states (inte bara s)
    for flight in s.states:
        
        # 4. Använd variabler som faktiskt finns i StateVector (t.ex. origin_country istället för estDepartureAirport)
        callsign = flight.callsign.strip() if flight.callsign else "Okänd"
        country = flight.origin_country
        altitude = flight.baro_altitude
        
        print(f"Flight: {callsign}, Registrerad i: {country}, Höjd: {altitude} meter")
        
else:
    print("Inga flyg hittades i boxen just nu, eller så slog vi i 10-sekundersspärren (Rate Limit).")
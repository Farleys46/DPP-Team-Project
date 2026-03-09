import requests
from fastapi import FastAPI
from openaq_API_KEY import OPENAQ_API_KEY

app = FastAPI()

@app.get("/air-quality")
def get_air_quality():
    
    url = "https://api.openaq.org/v3/locations/8118"
    
    headers = {
        "X-API-Key": OPENAQ_API_KEY
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Kunde inte hämta luftdata", "status_code": response.status_code}
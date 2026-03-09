import requests
from fastapi import FastAPI

app = FastAPI()

@app.get("/air-quality")
def get_air_quality():
    
    url = "https://api.openaq.org/v3/locations/8118"
    
    headers = {
        "X-API-Key": "354c9c799cd187a6eb4d889504b9cc382c6b8f64f215c474d4e3a7af7cc7572c"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Kunde inte hämta luftdata", "status_code": response.status_code}
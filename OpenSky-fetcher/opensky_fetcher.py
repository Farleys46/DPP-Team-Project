import os
import time
import json
from kafka import KafkaProducer
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
        producer = KafkaProducer(
            bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None
        )
        
        TOPIC = os.getenv("KAFKA_TOPIC", "flights.live")
        
        for flight in flight_data:
            producer.send(
                TOPIC,
                key=str(flight["callsign"]),
                value=flight
            )
        
        producer.flush()
        print(f"SKickade {len(flight_data)} flygdata till Kafka topic")
        
    except Exception as e:
        print(f"Ett fel uppstod med Kafka: {e}")
        
# Startar scriptet
if __name__ == "__main__":
    while True:
        get_and_store_flights()
        print("Klar, väntar 5min innan nästa hämtning av data!")
        time.sleep(300)
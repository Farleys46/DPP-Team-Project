import os
import json
import psycopg2
from kafka import KafkaConsumer
from dotenv import load_dotenv

load_dotenv()


def main():
    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    TOPIC = os.getenv("KAFKA_TOPIC", "flights.live")
    GROUP_ID = "flight-consumer-group"
    
    
    conn = psycopg2.connect(
        host="db",
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
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
    conn.commit()
    
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id = GROUP_ID,
        auto_offset_reset="latest",
        value_deserializer=lambda b: json.loads(b.decode("utf-8")),
        key_deserializer=lambda b: b.decode("utf-8") if b else None,
    )
    
    print(f"Lyssnar på topic: {TOPIC}")
    for msg in consumer:
        flight = msg.value
        
        cursor.execute("""
            INSERT INTO live_flights 
            (callsign, country, longitude, latitude, altitude_meters, velocity_m_s, flight_on_ground)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            flight.get("callsign"), flight.get("country"), flight.get("longitude"), 
            flight.get("latitude"), flight.get("altitude_meters"), 
            flight.get("velocity_m_s"), flight.get("flight_on_ground")
        ))
        conn.commit()
        
        print(f"Sparade flygdata i databasen")
        
if __name__ == "__main__":
    main()
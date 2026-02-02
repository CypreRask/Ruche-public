import requests
import time
import random

BACKEND_URL = "http://localhost:2000/api/lora-uplink"

print(f"Starting LoRaWAN simulator -> {BACKEND_URL}")

while True:
    temperature = 20.0 + random.uniform(-5.0, 5.0)
    mass = 30.0 + random.uniform(-1.0, 1.0)
    
    payload = {
        "temperature": round(temperature, 2),
        "mass": round(mass, 2)
    }
    
    try:
        response = requests.post(BACKEND_URL, json=payload, timeout=1)
        print(f"Sent: {payload} -> {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")
        
    time.sleep(5)

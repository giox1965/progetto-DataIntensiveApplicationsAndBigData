import socket
import json
import time
import random
import threading
from datetime import datetime

GATEWAY_IP = "127.0.0.1"
GATEWAY_PORT = 8081

class SensorMock:
    def __init__(self, sensor_id, sensor_type, base_val, location):
        self.sensor_id = sensor_id
        self.sensor_type = sensor_type
        self.base_val = base_val
        self.location = location
        self.running = True

    def generate_payload(self):
        """Logica di generazione dati grezzi"""
        variation = self.base_val * 0.1
        current_val = self.base_val + random.uniform(-variation, variation)
        
        if random.random() < 0.05:
            current_val += self.base_val * 1.5
            
        return {
            "sensor_id": self.sensor_id,
            "type": self.sensor_type,
            "value": round(current_val, 2),
            "location": self.location,
            "timestamp": datetime.now().isoformat(),
        }

    def start_sending(self):
        """Loop di invio tramite socket UDP"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        print(f"[*] Sensore {self.sensor_id} avviato.")
        
        try:
            while self.running:
                payload = self.generate_payload()
                message = json.dumps(payload).encode('utf-8')
                sock.sendto(message, (GATEWAY_IP, GATEWAY_PORT))
                
                time.sleep(random.uniform(1, 3))
        except Exception as e:
            print(f"[!] Errore sensore {self.sensor_id}: {e}")
        finally:
            sock.close()

if __name__ == "__main__":
    sensor_configs = [
        ("TEMP", "temperature", 22.0),
        ("HUM", "humidity", 45.0),
        ("PRES", "pressure", 1013.0),
        ("VIB", "vibration", 0.02),
        ("CURR", "current", 4.5),         
        ("VOLT", "voltage", 230.1),       
        ("TOL", "tolerance_gap", 0.05)    
    ]

    locations = ["impianto_1", "impianto_2", "impianto_3", "impianto_4", "impianto_5"]

    #threads = []

    print(f"--- MOCK AVVIATO ---")

    for location in locations:
        for sid, stype, base in sensor_configs:
            sensor = SensorMock(sid, stype, base, location)
            t = threading.Thread(target=sensor.start_sending, daemon=True)
            t.start()
            #threads.append(t)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n--- MOCK INTERROTTO ---")
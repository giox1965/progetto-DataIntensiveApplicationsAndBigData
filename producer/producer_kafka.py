from confluent_kafka import Producer
import socket
import json
import os
import sys

conf = {
    'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9091'),
    'client.id': socket.gethostname(),
    'acks': 'all' 
}

IP = str(os.getenv('SERVER_IP', '0.0.0.0'))
PORT = int(os.getenv('SERVER_PORT', 8081))

producer = Producer(conf)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    sock.bind((IP, PORT))
except Exception as e:
    print(f"Errore nel binding del socket: {e}")
    sys.exit(1)

def delivery_report(err, msg):
    if err is not None:
        print(f"[-] Errore nell'invio: {err}")
    else:
        print(f"[+] Prodotto su {msg.topic()} [Partizione: {msg.partition()}]")

print(f"--- Gateway sensori attivo su {IP}:{PORT} ---")
print(f"--- Connesso a Kafka: {conf['bootstrap.servers']} ---")

try:
    while True:
        data, addr = sock.recvfrom(1024)

        try:
            payload = json.loads(data.decode('utf-8'))
            
            sid = payload.get("sensor_id", "unknown")
            topic = payload.get("location", "N/A")
            
            producer.produce(
                topic, 
                key=str(sid).encode('utf-8'), 
                value=data, 
                callback=delivery_report
            )
            
            producer.poll(0)

        except json.JSONDecodeError:
            print(f"[!] Ricevuto dato non JSON da {addr}")
        except Exception as e:
            print(f"[!] Errore durante l'elaborazione: {e}")

except KeyboardInterrupt:
    print("\n[*] Spegnimento in corso...")
finally:
    sock.close()
    producer.flush()
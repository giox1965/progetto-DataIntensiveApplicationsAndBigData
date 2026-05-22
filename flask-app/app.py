from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient

app = Flask(__name__)
client = MongoClient('mongodb://admin:password@mongodb:27017/')
db = client.iot_database

@app.route('/')
def home():
    """Pagina principale."""
    current_host = request.host.split(':')[0]
    
    grafana_url = f"http://{current_host}:3000"

    return render_template('index.html', grafana_url=grafana_url)

# @app.route('/api/dati')
# def get_dati():
#     """API per recuperare gli ultimi dati di telemetria."""
#     dati = list(db.telemetria.find().sort("timestamp", -1).limit(10))
#     for doc in dati:
#         doc['_id'] = str(doc['_id'])
#     return jsonify(dati)

@app.route('/api/<impianto_id>/<sensor_id>/mean')
def get_mean(impianto_id, sensor_id):
    """API dinamica che restituisce la media dei dati raggruppati ogni 5 minuti per un singolo sensore."""

    try:
        collezione = db[impianto_id]
        
        pipeline = [
            {
                "$match": {
                    "sensor_id": sensor_id,
                }
            },
            
            {
                "$group": {
                    "_id": {
                        "sensor_id": "$sensor_id",
                        "finestra_tempo": {
                            "$dateTrunc": {
                                "date": {"$toDate": "$timestamp"},
                                "unit": "minute",
                                "binSize": 5 
                            }
                        }
                    },
                    "media_temperatura": {"$avg": "$value"}
                }
            },
            
            {"$sort": {"_id.finestra_tempo": 1}}
        ]
        
        dati = list(collezione.aggregate(pipeline))
        
        risultato = []
        for doc in dati:
            if doc["_id"]["finestra_tempo"] is None:
                continue 
                
            risultato.append({
                "timestamp": doc["_id"]["finestra_tempo"].isoformat(),
                "value": round(float(doc["media_temperatura"]), 2),
                "sensor_id": doc["_id"]["sensor_id"]
            })
            
        return jsonify(risultato)
        
    except Exception as e:
        return jsonify({"error": "Errore interno durante l'aggregazione dei dati", "dettaglio": str(e)}), 500

@app.route('/api/query_personalizzata', methods=['POST'])
def query_personalizzata():
    """
    Endpoint che accetta una query MongoDB dinamica su una collezione specifica.
    Esempio di payload JSON richiesto:
    {
        "impianto": "impianto_1",
        "filtro": {"type": "temperature", "value": {"$gt": 20}},
        "ordinamento": "timestamp",
        "direzione": -1,
        "limite": 50
    }
    """
    try:
        content = request.get_json(silent=True)
        if not content:
            return jsonify({"error": "Payload JSON mancante o non valido"}), 400

        collezioni_permesse = ["impianto_1", "impianto_2", "impianto_3", "impianto_4", "impianto_5"]
        
        nome_impianto = content.get('impianto')
        if not nome_impianto:
            return jsonify({"error": "Il campo 'impianto' è obbligatorio"}), 400
            
        if nome_impianto not in collezioni_permesse:
            return jsonify({"error": f"Impianto non valido. Scegli tra: {', '.join(collezioni_permesse)}"}), 400

        filtro = content.get('filtro', {})
        ordinamento = content.get('ordinamento', 'timestamp')
        direzione = content.get('direzione', -1)
        limite = min(int(content.get('limite', 10)), 500)

        collezione = db[nome_impianto]
        cursore = collezione.find(filtro).sort(ordinamento, direzione).limit(limite)
        
        risultato = list(cursore)

        for doc in risultato:
            doc['_id'] = str(doc['_id'])

        return jsonify(risultato)

    except Exception as e:
        return jsonify({"error": f"Errore nell'esecuzione della query: {str(e)}"}), 400
    
@app.route('/api/impianti')
def get_impianti():
    """API che restituisce la lista degli impianti presenti nel database."""
    try:
        collezioni = db.list_collection_names()
        
        return jsonify(collezioni)
        
    except Exception as e:
        return jsonify({"error": "Errore nel recupero degli impianti", "dettaglio": str(e)}), 500

@app.route('/api/<impianto_id>/sensori')
def get_sensori(impianto_id):
    """API che restituisce la lista dei sensori unici presenti in un impianto."""
    collezione = db[impianto_id]

    try:
        
        lista_sensori = collezione.distinct("sensor_id")
        
        return jsonify(lista_sensori)
        
    except Exception as e:
        return jsonify({"error": "Errore nel recupero dei sensori", "dettaglio": str(e)}), 500

# @app.route('/api/kafka/topics')
# def get_topic():
#     """API che restituisce il topic Kafka attualmente in uso."""

#     return jsonify({"topic": db.get_collection()}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)